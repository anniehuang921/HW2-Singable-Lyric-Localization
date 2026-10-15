import copy
import json
import tempfile
import unittest
from pathlib import Path
from hw2_translation.controller import Controller
from synthetic_fixtures import read_catalog, ROOT as DEFAULT_ROOT, comparison
from hw2_ui.presenter import Presenter

class SavedTranslationTests(unittest.TestCase):
    def setUp(self):
        self.record=comparison()
        self.presenter=Presenter(read_catalog(),{'yingmusic_official':DEFAULT_ROOT})
    def test_read_saved_without_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'comparison-fixture.json';path.write_text(json.dumps(self.record))
            def forbidden():raise AssertionError('provider must not be used')
            r=Controller(self.presenter,provider_factory=forbidden,directory=Path(directory)).load_saved('SingEdit_EN_01')
            self.assertEqual(r['source'],self.record['source']);self.assertEqual(r['artifact_path'],str(path.resolve()))
    def test_mock_wrong_model_and_wrong_source_rejected(self):
        for field,value in [('is_mock',True),('source',['unrelated'])]:
            with tempfile.TemporaryDirectory() as directory:
                record=copy.deepcopy(self.record);record[field]=value
                (Path(directory)/'comparison-fixture.json').write_text(json.dumps(record))
                with self.assertRaises(ValueError):Controller(self.presenter,directory=Path(directory)).load_saved('SingEdit_EN_01')
        with tempfile.TemporaryDirectory() as directory:
            record=copy.deepcopy(self.record);record['provider']['model']='gemini-3.8-flash'
            (Path(directory)/'comparison-fixture.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):Controller(self.presenter,directory=Path(directory)).load_saved('SingEdit_EN_01')
    def test_incomplete_demo_rejected(self):
        with self.assertRaises(ValueError):Controller(self.presenter).load_saved('melody_control_EN_01')
