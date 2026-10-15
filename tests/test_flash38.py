import json
import os
import unittest
from unittest.mock import patch
import httpx
import hw2_translation.providers as module
from hw2_translation.providers import CompatibleProvider,Settings,ProviderError

class Flash38Tests(unittest.TestCase):
    def setUp(self):module._REQUESTS=0;module._HALTED=False
    def tearDown(self):module._REQUESTS=0;module._HALTED=False
    def test_low_settings_model_usage(self):
        def handler(request):
            data=json.loads(request.content)
            self.assertEqual(data['model'],'gemini-3.8-flash');self.assertEqual(data['reasoning_effort'],'low');self.assertEqual(data['max_tokens'],4096)
            return httpx.Response(200,json={'model':'gemini-3.8-flash','usage':{'prompt_tokens':5,'completion_tokens':2,'total_tokens':7,'private':'not stored'},'choices':[{'message':{'content':'OK'},'finish_reason':'stop'}]})
        p=CompatibleProvider(Settings('https://generativelanguage.googleapis.com/v1beta/openai/','gemini-3.8-flash',max_tokens=4096,reasoning_effort='low'),httpx.MockTransport(handler))
        self.assertEqual(p.generate('Reply with OK.'),'OK');self.assertEqual(p.last_response['http_status'],200)
        self.assertEqual(p.last_response['usage'],{'prompt_tokens':5,'completion_tokens':2,'total_tokens':7})
    def test_process_budget_across_instances(self):
        calls=[]
        def handler(request):calls.append(1);return httpx.Response(200,json={'choices':[{'message':{'content':'OK'}}]})
        with patch.dict(os.environ,{'HW2_LLM_REQUEST_LIMIT':'1'}):
            p=CompatibleProvider(Settings('http://127.0.0.1','fixture'),httpx.MockTransport(handler));p.generate('test')
            with self.assertRaises(ProviderError):CompatibleProvider(p.settings,p.transport).generate('test')
        self.assertEqual(len(calls),1)
    def test_error_array_halts_all_later_requests(self):
        calls=[]
        def handler(request):calls.append(1);return httpx.Response(429,json=[{'error':{'code':429,'status':'RESOURCE_EXHAUSTED','message':'quota'}}])
        with patch.dict(os.environ,{'HW2_LLM_REQUEST_LIMIT':'8'}):
            p=CompatibleProvider(Settings('http://127.0.0.1','fixture'),httpx.MockTransport(handler))
            with self.assertRaises(ProviderError) as exc:p.generate('test')
            self.assertEqual(exc.exception.details['google_status'],'RESOURCE_EXHAUSTED')
            with self.assertRaises(ProviderError):p.generate('test')
        self.assertEqual(len(calls),1)
