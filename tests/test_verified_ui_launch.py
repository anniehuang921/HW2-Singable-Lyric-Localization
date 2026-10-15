import copy
import json
from pathlib import Path
import unittest
from hw2_translation.verify_preflight import verify
from synthetic_fixtures import success_evidence

class VerifiedLaunchTests(unittest.TestCase):
    def test_synthetic_success_schema_with_dot_accepted(self):verify(success_evidence())
    def test_mock_error_wrong_model_and_settings_rejected(self):
        original=success_evidence()
        cases=[]
        for field,value in [('is_mock',True),('model_confirmed',False),('safe_reply','Not OK')]:
            r=copy.deepcopy(original);r[field]=value;cases.append(r)
        r=copy.deepcopy(original);r['api_response']['http_status']=503;cases.append(r)
        r=copy.deepcopy(original);r['provider']['model']='gemini-3.8-flash';cases.append(r)
        r=copy.deepcopy(original);r['provider']['max_tokens']=1024;cases.append(r)
        for record in cases:
            with self.assertRaises(ValueError):verify(record)
    def test_missing_evidence_fields_rejected(self):
        with self.assertRaises(ValueError):verify({})
