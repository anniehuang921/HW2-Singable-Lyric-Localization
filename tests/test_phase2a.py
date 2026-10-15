"""Offline tests for official provenance, filters, audio, and missing materials."""
import dataclasses
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
from hw2_ui.catalog import DEFAULT_ROOT, Demo, asset_info, availability, build_catalog, read_catalog, safe_asset
from hw2_ui.presenter import Presenter

@unittest.skipUnless((DEFAULT_ROOT/'app_local.py').is_file(), 'Requires local official YingMusic repository and example audio')
class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demos = read_catalog()
        cls.presenter = Presenter(cls.demos, {'yingmusic_official': DEFAULT_ROOT})

    def test_official_catalog_matches_literal_presets(self):
        self.assertEqual([dataclasses.asdict(d) for d in self.demos], build_catalog()['demos'])
        self.assertEqual(len(self.demos), 8)
        self.assertEqual(sum(d.language == 'en' for d in self.demos), 4)

    def test_lyric_edit_provenance_not_target(self):
        for d in self.demos:
            if d.task == 'Lyric Editing':
                self.assertEqual(d.original_audio, d.timbre_audio)
                self.assertEqual(d.original_segments, d.reference_text.split('|'))
                self.assertNotEqual(d.original_lyrics, d.official_target_text.replace('|', '\n'))
                self.assertTrue(availability(d, DEFAULT_ROOT)['complete'])

    def test_melody_ref_not_assumed_original(self):
        for d in self.demos:
            if d.task == 'Melody Control':
                self.assertIsNone(d.original_segments)
                self.assertNotEqual(d.melody_audio, d.timbre_audio)
                self.assertFalse(availability(d, DEFAULT_ROOT)['complete'])

    def test_searchable_dropdown_choices_and_filters(self):
        self.assertEqual(len(self.presenter.choices()), 4)
        self.assertEqual(len(self.presenter.choices('zh', 'Lyric Editing')), 2)
        self.assertEqual(len(self.presenter.choices('全部')), 8)
        self.assertEqual(self.presenter.choices('fr'), [])
        self.assertEqual(self.presenter.choices()[0][1], 'SingEdit_EN_01')

    def test_selection_switch_and_boundaries(self):
        for d in self.demos:
            values = self.presenter.select(d.id)
            self.assertEqual(values[1], d.original_lyrics)
            self.assertEqual(values[6]['demo_id'], d.id)
            self.assertEqual(values[6]['line_count'], len(d.original_segments) if d.original_segments else None)
            if d.melody_audio == d.timbre_audio:
                self.assertIsNone(values[3])
            else:
                self.assertIsNotNone(values[3])
        self.assertEqual(self.presenter.select('unknown')[1:6], ('', None, None, None, ''))

    def test_all_official_audio_decode_and_pcm_playback(self):
        checked = set()
        for d in self.demos:
            for key in ['original_audio', 'melody_audio', 'timbre_audio']:
                relative = getattr(d, key)
                if relative in checked:
                    continue
                checked.add(relative)
                info = asset_info(DEFAULT_ROOT, relative)
                self.assertTrue(info['available'])
                source, sr = sf.read(DEFAULT_ROOT / relative, always_2d=True)
                cache = self.presenter.audio(d, key, info)
                decoded, rate = sf.read(cache, always_2d=True)
                self.assertEqual(rate, sr)
                self.assertEqual(source.shape, decoded.shape)
                self.assertEqual(sf.info(cache).subtype, 'PCM_16')
                self.assertTrue(np.isfinite(decoded).all())
                self.assertGreater(np.max(np.abs(decoded)), 0)
                self.assertLess(np.max(np.abs(np.clip(source, -1, 1-1/32768) - decoded)), 1/32768 + 1e-6)
        self.assertEqual(len(checked), 12)

    def test_missing_root_clears_audio(self):
        p = Presenter(self.demos, {'yingmusic_official': Path('/tmp/hw2-nonexistent-material-root')})
        result = p.select('SingEdit_EN_01')
        self.assertEqual(result[2:5], (None, None, None))
        self.assertFalse(result[6]['complete'])
        self.assertIn('素材路徑不存在', result[0])

    def test_invalid_audio_and_no_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'bad.wav').write_text('not audio')
            self.assertFalse(asset_info(root, 'bad.wav')['available'])
            self.assertFalse(asset_info(root, None)['available'])
            self.assertFalse(asset_info(root, '../escape.wav')['available'])

    def test_invalid_id_and_empty_choice_no_stale_lyrics(self):
        self.assertEqual(self.presenter.select(None)[1], '')
        self.assertEqual(self.presenter.select('missing')[6], {})

    def test_source_independent_schema(self):
        d = dataclasses.replace(self.demos[0], source_type='future_youtube', source_url='https://example.test/source')
        p = Presenter([d], {'future_youtube': DEFAULT_ROOT})
        self.assertEqual(p.select(d.id)[6]['source_type'], 'future_youtube')

if __name__ == '__main__':
    unittest.main()
