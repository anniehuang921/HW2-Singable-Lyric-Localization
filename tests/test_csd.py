"""Original synthetic CSD fixtures only; no redistributed official content."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
from hw2_datasets.csd import CSD
from hw2_datasets.presenter import DatasetPresenter
from synthetic_fixtures import ROOT,read_catalog


def fixture(root):
    for folder,prefix in [('english','en'),('korean','kr')]:
        metadata={}
        for key in 'ab':
            stem=prefix+'001'+key
            metadata[stem]={'songname':'Synthetic river','key_diff':0 if key=='a' else -2,'tempo':100,'time_signature':'4/4'}
            for kind in ['wav','mid','csv','lyric','txt']:(root/folder/kind).mkdir(parents=True,exist_ok=True)
            sf.write(root/folder/'wav'/f'{stem}.wav',np.sin(np.arange(4410)*0.1)*0.1,44100,subtype='PCM_16')
            (root/folder/'lyric'/f'{stem}.txt').write_text('Silver river\n\nClouds above\n' if prefix=='en' else '합성 노래\n\n시험\n')
            (root/folder/'txt'/f'{stem}.txt').write_text('s_i')
            (root/folder/'csv'/f'{stem}.csv').write_text('start,end,pitch,syllable\n0.01,0.09,60,s_i\n')
            # One synthetic note, standard MIDI format 0.
            track=bytes.fromhex('00 90 3c 40 60 80 3c 00 00 ff 2f 00')
            (root/folder/'mid'/f'{stem}.mid').write_bytes(b'MThd'+(6).to_bytes(4,'big')+bytes.fromhex('0000 0001 0060')+b'MTrk'+len(track).to_bytes(4,'big')+track)
        (root/folder/'metadata.json').write_text(json.dumps(metadata))

class CSDTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);fixture(self.root);self.csd=CSD(self.root)
    def test_song_recording_distinction_and_keys(self):
        self.assertEqual(len(self.csd.recordings),4)
        self.assertEqual(len(self.csd.songs('全部')),2)
        self.assertEqual([x[1] for x in self.csd.variants('CSD_en001')],['CSD_en001a','CSD_en001b'])
        self.assertEqual(self.csd.songs('ko')[0][1],'CSD_kr001')
    def test_exact_lyrics_and_annotation_binding(self):
        r=self.csd.recordings['CSD_en001a'];self.assertIn('\n\n',r.lyrics)
        for rel in [r.audio_path,*r.annotations.values()]:self.assertEqual(Path(rel).stem,'en001a')
        self.assertEqual(r.to_demo().original_segments,['Silver river','Clouds above'])
        self.assertEqual(r.to_demo().reference_text,'Silver river|Clouds above')
        self.assertIn('待驗證',self.csd.details('CSD_kr001b')['translation_status'])
    def test_presenter_and_original_demo_filters(self):
        p=DatasetPresenter(read_catalog(),{'yingmusic_official':ROOT},self.csd)
        self.assertEqual(len(p.choices()),4)
        for rid,r in self.csd.recordings.items():
            view=p.select(rid);self.assertEqual(view[1],r.lyrics);self.assertTrue(Path(view[2]).is_file())
            self.assertEqual(view[6]['recording_id'],rid)
            self.assertEqual(view[6]['song_id'],r.song_id)
        self.assertEqual(p.select('missing')[2:5],(None,None,None))
    def test_missing_pair_and_missing_root(self):
        (self.root/'english/mid/en001b.mid').unlink()
        with self.assertRaisesRegex(ValueError,'缺失'):CSD(self.root)
        with self.assertRaisesRegex(ValueError,'尚未安裝'):CSD(self.root/'absent')
    def test_missing_key_and_unlisted_audio(self):
        p=self.root/'english/metadata.json';data=json.loads(p.read_text());del data['en001b'];p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'不一致'):CSD(self.root)
    def test_path_escape_rejected(self):
        target=self.root/'outside.txt';target.write_text('synthetic')
        path=self.root/'english/lyric/en001a.txt';path.unlink();path.symlink_to('/tmp/outside-csd-fixture.txt')
        with self.assertRaisesRegex(ValueError,'超出'):CSD(self.root)
    def test_case_only_official_title_difference_does_not_duplicate_song(self):
        path=self.root/'english/metadata.json';data=json.loads(path.read_text());data['en001b']['songname']='synthetic river';path.write_text(json.dumps(data))
        c=CSD(self.root);self.assertEqual(len(c.songs('en')),1)
        self.assertEqual(c.recordings['CSD_en001b'].metadata['songname'],'synthetic river')
    def test_standard_midi_note_reader(self):
        from hw2_datasets.verify_csd import midi_notes
        self.assertEqual(midi_notes(self.root/'english/mid/en001a.mid'),1)
    def test_ui_build_has_sources_and_existing_events(self):
        from hw2_ui.app import build_ui
        p=DatasetPresenter(read_catalog(),{'yingmusic_official':ROOT},self.csd)
        with patch.dict('os.environ',{'HW2_SINGING_ENABLED':'0'}):app=build_ui(p,saved_only=True,singing=True)
        names={d.get('api_name') for d in app.config['dependencies']}
        self.assertTrue({'select_demo','select_source','csd_language','csd_song','load_saved_translation','load_saved_singing','generate_singing'}<=names)
        app.close()

if __name__=='__main__':unittest.main()
