import json
import unittest
import httpx
from hw2_translation.providers import completion_url,safe_http_error,CompatibleProvider,Settings,ProviderError

class DiagnosticTests(unittest.TestCase):
    def test_url_with_and_without_slash(self):
        base='https://generativelanguage.googleapis.com/v1beta/openai'
        for value in [base,base+'/',base+'///']:
            self.assertEqual(completion_url(value),base+'/chat/completions')
    def test_actual_mock_request_path(self):
        def handler(request):
            self.assertEqual(request.url.scheme,'https')
            self.assertEqual(request.url.host,'generativelanguage.googleapis.com')
            self.assertEqual(request.url.path,'/v1beta/openai/chat/completions')
            return httpx.Response(404,json={'error':{'code':404,'status':'NOT_FOUND','message':'model not accessible'}})
        p=CompatibleProvider(Settings('https://generativelanguage.googleapis.com/v1beta/openai/','gemini-2.5-flash'),httpx.MockTransport(handler))
        with self.assertRaises(ProviderError) as c:p.generate('mock')
        self.assertEqual(c.exception.details['google_status'],'NOT_FOUND')
    def test_redaction_and_length(self):
        secret='TEST-SECRET-ONLY'
        message=secret+' API_KEY=other-private-key\nAuthorization: Bearer anything\n'+('x'*1000)
        error=safe_http_error(httpx.Response(403,json={'error':{'status':'PERMISSION_DENIED','code':403,'message':message},'headers':{'Authorization':secret}}),secret)
        self.assertNotIn(secret,str(error));self.assertNotIn('other-private-key',str(error));self.assertNotIn('Bearer',str(error))
        self.assertLessEqual(len(error.details['google_message']),400)
    def test_non_json_oversized_and_unexpected_fields(self):
        for response in [httpx.Response(429,text='Authorization: sensitive'),httpx.Response(404,content=b'x'*20000),httpx.Response(404,json={'error':['secret']})]:
            self.assertEqual(safe_http_error(response).details,{'http_status':response.status_code})
