"""Public, synthetic coverage independent of YingMusic checkout and API credentials."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from hw2_ui.catalog import read_catalog
from hw2_ui.presenter import Presenter
from synthetic_fixtures import read_catalog as fixtures, ROOT

class PublicCatalogTests(unittest.TestCase):
    def test_filters_selection_missing_audio_and_boundary(self):
        p=Presenter(fixtures(),{'yingmusic_official':ROOT})
        self.assertEqual(len(p.choices()),4)
        self.assertEqual(len(p.choices('zh','Lyric Editing')),2)
        for d in fixtures():
            r=p.select(d.id)
            self.assertEqual(r[1],d.original_lyrics)
            self.assertEqual(r[6]['demo_id'],d.id)
        self.assertEqual(p.select('unknown')[1],'')
        with tempfile.TemporaryDirectory() as empty:
            r=Presenter(fixtures(),{'yingmusic_official':Path(empty)}).select('SingEdit_EN_01')
            self.assertEqual(r[2:5],(None,None,None))
            self.assertFalse(r[6]['complete'])
    def test_default_reads_local_presets_not_private_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            rows=[['sample.wav','sample.wav','Synthetic first|Synthetic second','合成目標',0,0,0,0,0,0,0]]
            (root/'app_local.py').write_text('EXAMPLES_LYRIC_EDIT = '+repr(rows)+'\nEXAMPLES_MELODY_CONTROL = []\nraise RuntimeError("must not execute")\n')
            with patch('hw2_ui.catalog.subprocess.check_output',return_value='synthetic\n'):
                demos=read_catalog(root=root)
            self.assertEqual(demos[0].original_segments,['Synthetic first','Synthetic second'])
    def test_explicit_snapshot_schema_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'fixture.json';p.write_text(json.dumps({'schema_version':2,'demos':[]}))
            with self.assertRaises(ValueError):read_catalog(p)
