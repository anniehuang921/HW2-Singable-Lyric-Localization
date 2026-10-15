"""Mock-only generation tests; BLT bridge calls are real original algorithms."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from synthetic_fixtures import read_catalog, ROOT as DEFAULT_ROOT
from hw2_ui.presenter import Presenter
from hw2_translation.providers import MockProvider, CompatibleProvider, Settings, ProviderError, from_environment
from hw2_translation.engine import Engine, parse_output
from hw2_translation.blt_bridge import Bridge
from hw2_translation.controller import Controller

class TranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demos={d.id:d for d in read_catalog()};cls.bridge=Bridge()
    def output(self,demo,lines):
        return json.dumps({'segments':[{'id':f'{demo.id}:{i+1:03d}','text':line} for i,line in enumerate(lines)]},ensure_ascii=False)
    def test_both_english_demo_flows_same_model_and_budget(self):
        for name in ['SingEdit_EN_01','SingEdit_EN_02']:
            demo=self.demos[name];lines=['測試']*len(demo.original_segments)
            raw=self.output(demo,lines);provider=MockProvider([raw]*4)
            result=Engine(provider,self.bridge).run(demo)
            self.assertTrue(result['is_mock']);self.assertEqual(len(provider.prompts),4)
            self.assertNotIn('target_syllables',provider.prompts[0]);self.assertIn('target_syllables',provider.prompts[1])
            self.assertEqual(result['modes']['blt_assisted']['revisions'],2)
            self.assertEqual(result['modes']['blt_assisted']['status'],'revision_limit_reached')
            self.assertEqual(result['segment_ids'],[f'{name}:{i+1:03d}' for i in range(len(lines))])
    def test_real_original_blt_analysis_and_validator(self):
        result=self.bridge.analyze(['Let it go']);self.assertEqual(result['target_syllables'],[3])
        result=self.bridge.validate(['Let it go'],['隨它吧']);self.assertTrue(result['syllables_match']);self.assertTrue(result['han_only'])
    def test_revision_success_stops_early(self):
        demo=self.demos['SingEdit_EN_01'];constraints=self.bridge.analyze(demo.original_segments)
        bad=self.output(demo,['測試']*len(demo.original_segments))
        labels={};ending=['風','花','冬','海']
        lines=[]
        for count,label in zip(constraints['target_syllables'],constraints['rhyme_scheme']):
            labels.setdefault(label,ending[len(labels)])
            lines.append('春'*(count-1)+labels[label])
        good=self.output(demo,lines);provider=MockProvider([bad,bad,good])
        result=Engine(provider,self.bridge).run(demo)
        self.assertEqual(result['modes']['blt_assisted']['status'],'completed')
        self.assertEqual(result['modes']['blt_assisted']['revisions'],1)
        self.assertEqual(len(provider.prompts),3)

    def test_missing_configuration(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(ProviderError):from_environment()
    def test_invalid_output_segment_ids_and_count(self):
        for raw in ['not JSON','{"segments":[]}',self.output(self.demos['SingEdit_EN_01'],['測試'])]:
            with self.assertRaises(ProviderError):parse_output(raw,['SingEdit_EN_01:001','SingEdit_EN_01:002'])
    def test_provider_http_errors_timeout_and_key_not_metadata(self):
        def timeout(request):raise httpx.ReadTimeout('private detail')
        for transport in [httpx.MockTransport(timeout),httpx.MockTransport(lambda r:httpx.Response(401))]:
            provider=CompatibleProvider(Settings('http://127.0.0.1:9999/v1','fixture',api_key='TEST-ONLY-SECRET'),transport)
            self.assertNotIn('TEST-ONLY-SECRET',str(provider.metadata()))
            with self.assertRaises(ProviderError):provider.generate('fixture')
    def test_same_endpoint_settings_and_response_parsing(self):
        def handler(request):
            body=json.loads(request.content);self.assertEqual(body['model'],'fixture')
            return httpx.Response(200,json={'choices':[{'message':{'content':'fixture'}}]})
        self.assertEqual(CompatibleProvider(Settings('http://127.0.0.1:9999/v1','fixture'),httpx.MockTransport(handler)).generate('test'),'fixture')
    def test_traditional_display_preserves_raw(self):
        demo=self.demos['SingEdit_EN_01'];raw=self.output(demo,['测试','歌词'])
        self.assertEqual(parse_output(raw,['SingEdit_EN_01:001','SingEdit_EN_01:002']),['測試','歌詞'])
    def test_manual_edit_validation_saved_and_wrong_demo_rejected(self):
        demo=self.demos['SingEdit_EN_01'];raw=self.output(demo,['測試','歌詞'])
        with tempfile.TemporaryDirectory() as directory:
            controller=Controller(Presenter(read_catalog(),{'yingmusic_official':DEFAULT_ROOT}),lambda:MockProvider([raw]*4),directory=Path(directory))
            record=controller.translate(demo.id)
            edit,path=controller.edit(demo.id,record,'direct','人工修改\n中文歌詞')
            self.assertEqual(edit['before'],['測試','歌詞']);self.assertEqual(edit['after'],['人工修改','中文歌詞']);self.assertTrue(Path(path).is_file())
            with self.assertRaises(ValueError):controller.edit('SingEdit_EN_02',record,'direct','詞')
            with self.assertRaises(ValueError):controller.edit(demo.id,record,'direct','詞')
    def test_failure_stops_requests_and_preserves_attempt(self):
        result=Engine(MockProvider(['invalid JSON']),self.bridge).run(self.demos['SingEdit_EN_01'])
        self.assertEqual(result['modes']['direct']['status'],'failed');self.assertNotIn('blt_assisted',result['modes'])
        self.assertEqual(result['modes']['direct']['attempts'][0]['raw_output'],'invalid JSON')
    def test_non_english_or_incomplete_rejected(self):
        for name in ['SingEdit_ZH_01','melody_control_EN_01']:
            with self.assertRaises(ProviderError):Engine(MockProvider([]),self.bridge).run(self.demos[name])
    def test_revisions_hard_cap(self):
        with self.assertRaises(ValueError):Engine(MockProvider([]),self.bridge,max_revisions=3)

if __name__=='__main__':unittest.main()
