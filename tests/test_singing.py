"""Synthetic adapter checks; no weights, torch, GPU, API or fake singing."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import soundfile as sf
from synthetic_fixtures import ROOT, read_catalog, comparison
from hw2_ui.presenter import Presenter
from hw2_singing.adapter import Settings,prepare,configuration,MockAdapter,SingingController,validate_output

class SingingTests(unittest.TestCase):
    def setUp(self):self.presenter=Presenter(read_catalog(),{'yingmusic_official':ROOT});self.record=comparison()
    def prepare(self,**kwargs):return prepare(self.presenter,self.record['demo_id'],self.record,**kwargs)
    def test_audio_and_reference_mapping_and_temporary_simplification(self):
        self.record['modes']['blt_assisted']['segments']=['測試樂聲','風裡飛翔']
        before=copy.deepcopy(self.record)
        r=self.prepare(candidate='blt_assisted')
        self.assertEqual(r['target_text'],'测试乐声|风里飞翔')
        self.assertEqual(r['selected_traditional_segments'],['測試樂聲','風裡飛翔'])
        self.assertEqual(r['original_reference_lyrics'],read_catalog()[0].reference_text)
        self.assertEqual(r['melody_audio'],str(ROOT/'reference.wav'))
        self.assertEqual(self.record,before)
    def test_wrong_demo_ids_source_count_and_empty_rejected(self):
        for field,value in [('demo_id','other'),('source',['wrong']),('segment_ids',['wrong'])]:
            r=copy.deepcopy(self.record);r[field]=value
            with self.assertRaises(ValueError):prepare(self.presenter,'SingEdit_EN_01',r,'direct')
        for lines in [['文字'],['文字',''],['文字|文字','測試']]:
            r=copy.deepcopy(self.record);r['modes']['direct']['segments']=lines
            with self.assertRaises(ValueError):prepare(self.presenter,'SingEdit_EN_01',r,'direct')
    def test_edit_snapshot_and_missing_audio(self):
        with self.assertRaises(ValueError):self.prepare(candidate='edited',edited='人工\n修改')
        r=self.prepare(candidate='edited',edited='人工\n修改',before={'demo_id':'SingEdit_EN_01'})
        self.assertEqual(r['target_text'],'人工|修改')
        with tempfile.TemporaryDirectory() as d:
            p=Presenter(read_catalog(),{'yingmusic_official':Path(d)})
            with self.assertRaises(ValueError):prepare(p,'SingEdit_EN_01',self.record,'direct')
    def test_mock_has_no_audio_and_records_request(self):
        with tempfile.TemporaryDirectory() as d:
            result=SingingController(self.presenter,MockAdapter(),Path(d)).generate('SingEdit_EN_01',self.record,'blt_assisted')
            self.assertTrue(result['is_mock']);self.assertIsNone(result['audio']);self.assertEqual(result['status'],'mock_validated')
            self.assertTrue(Path(result['artifact_path']).is_file());self.assertEqual(list(Path(d).rglob('*.wav')),[])
    def test_missing_models_fail_without_launching_worker(self):
        with patch.dict(os.environ,{},clear=True),tempfile.TemporaryDirectory() as d,patch('hw2_singing.adapter.subprocess.run') as run:
            self.assertFalse(configuration()['ready'])
            r=SingingController(self.presenter,directory=Path(d)).generate('SingEdit_EN_01',self.record,'direct')
            self.assertEqual(r['status'],'failed');self.assertIsNone(r['audio']);run.assert_not_called()
    def test_settings_bounds_and_audio_format(self):
        for settings in [Settings(seed=-1),Settings(nfe_step=100),Settings(separate_vocals=False)]:
            with self.assertRaises(ValueError):settings.validate()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'synthetic-tone.wav'
            sf.write(path,np.sin(np.arange(4410)*0.1)*0.1,44100)
            self.assertEqual(validate_output(path)['frames'],4410)
            sf.write(path,np.zeros(100),44100)
            with self.assertRaises(ValueError):validate_output(path)

    def test_malformed_manifest_is_a_safe_readiness_error(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'manifest.json';path.write_text('[]')
            with patch.dict(os.environ,{'HW2_SINGING_MANIFEST':str(path)},clear=True):
                self.assertFalse(configuration()['ready'])

    def test_load_saved_audio_checks_request_hash_and_never_calls_model(self):
        from hw2_singing.adapter import MODEL_ID
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);job=root/'fixture';job.mkdir();audio=job/'singing.wav'
            sf.write(audio,np.sin(np.arange(4410)*0.1)*0.1,44100)
            request=self.prepare(candidate='blt_assisted')
            result={'status':'completed','is_mock':False,'model_id':MODEL_ID,'revision':'synthetic-fixture','request':request,'audio':str(audio.resolve()),'audio_info':validate_output(audio)}
            (job/'result.json').write_text(json.dumps(result))
            singer=SingingController(self.presenter,MockAdapter(),root)
            with patch('hw2_singing.adapter.configuration',return_value={'manifest':{}}):
                self.assertEqual(singer.load_saved('SingEdit_EN_01',self.record,'blt_assisted')['audio'],str(audio.resolve()))
                with self.assertRaises(ValueError):singer.load_saved('SingEdit_EN_01',self.record,'direct')
                sf.write(audio,np.zeros(4410),44100)
                with self.assertRaises(ValueError):singer.load_saved('SingEdit_EN_01',self.record,'blt_assisted')
