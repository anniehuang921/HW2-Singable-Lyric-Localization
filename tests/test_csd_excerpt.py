"""Phase4B synthetic-only safety and source/parameter parity tests."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_csd import fixture
from synthetic_fixtures import ROOT,read_catalog
from hw2_datasets.csd import CSD
from hw2_datasets.presenter import DatasetPresenter
from hw2_singing.adapter import prepare,Settings
from hw2_datasets.workflow import ExcerptController,ExcerptSinger

class ExcerptTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);fixture(self.root)
  c=CSD(self.root);self.p=DatasetPresenter(read_catalog(),{'yingmusic_official':ROOT},c)
  r=c.recordings['CSD_en001a'];audio=self.root/r.audio_path
  self.audit={'recording_id':r.recording_id,'audio_path':str(audio),'audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'segments':['Silver river','Clouds above'],'start_seconds':0,'end_seconds':0.1}
  self.p.enable_excerpt(self.audit);rid=r.recording_id
  self.record={'demo_id':rid,'source':self.audit['segments'],'segment_ids':[rid+':001',rid+':002'],'is_mock':False,
    'modes':{m:{'segments':['銀河閃耀','雲在天空']} for m in ['direct','blt_assisted']}}
 def test_only_excerpt_is_actionable_and_full_song_remains_visible(self):
  self.assertTrue(self.p.actionable('CSD_en001a'));self.assertFalse(self.p.actionable('CSD_en001b'));self.assertFalse(self.p.actionable('CSD_kr001a'))
  self.assertEqual(self.p.select('CSD_en001a')[1],self.p.csd.recordings['CSD_en001a'].lyrics)
  self.assertEqual(self.p.demos['CSD_en001a'].original_segments,self.audit['segments'])
 def test_equal_inputs_and_pure_vocal_settings_for_both_modes(self):
  a=prepare(self.p,self.record['demo_id'],self.record,'direct');b=prepare(self.p,self.record['demo_id'],self.record,'blt_assisted')
  for key in ['original_audio','melody_audio','timbre_audio','original_reference_lyrics','settings','input_audio_sha256']:
   self.assertEqual(a[key],b[key])
  self.assertFalse(a['settings']['separate_vocals']);self.assertFalse(a['settings']['mix_accompaniment'])
  self.assertEqual(a['original_reference_lyrics'],'Silver river|Clouds above')
  with self.assertRaises(ValueError):prepare(self.p,self.record['demo_id'],self.record,'direct',settings=Settings())
 def test_tampered_excerpt_rejected_before_worker(self):
  self.audit['audio_sha256']='wrong'
  with self.assertRaisesRegex(ValueError,'不符'):prepare(self.p,self.record['demo_id'],self.record,'direct')
 def test_no_other_song_api_calls(self):
  factory=unittest.mock.Mock()
  c=ExcerptController(self.p,provider_factory=factory)
  with self.assertRaises(ValueError):c.translate('CSD_kr001a')
  with self.assertRaises(ValueError):c.translate('SingEdit_EN_01')
  factory.assert_not_called()
 def test_saved_singing_never_runs_worker(self):
  s=ExcerptSinger(self.p)
  with patch.object(s,'load_saved',return_value={'status':'completed','is_mock':False}) as load,patch('hw2_singing.adapter.NativeAdapter.run') as run:
   result=s.generate('CSD_en042a',self.record,'direct');self.assertEqual(result['status'],'completed');load.assert_called_once();run.assert_not_called()
 def test_midi_actual_time_parser_synthetic_note(self):
  from hw2_datasets.excerpt import midi_events
  notes=midi_events(self.root/'english/mid/en001a.mid');self.assertEqual(len(notes),1)
  self.assertEqual(notes[0],{'start':0.0,'end':0.5,'pitch':60})

if __name__=='__main__':unittest.main()
