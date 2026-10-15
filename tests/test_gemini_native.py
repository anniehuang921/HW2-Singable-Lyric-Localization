import unittest
import httpx
from hw2_translation.diagnose_gemini_native import diagnose,URL

class NativeTests(unittest.TestCase):
    def run_response(self,response):
        calls=[]
        def handler(request):
            calls.append(request)
            self.assertEqual(str(request.url),URL)
            self.assertEqual(request.method,'POST')
            self.assertNotIn('test-secret',str(request.url))
            import json
            self.assertEqual(json.loads(request.content)['generationConfig']['maxOutputTokens'],16)
            return response
        result=diagnose('test-secret',httpx.MockTransport(handler))
        self.assertEqual(len(calls),1);self.assertTrue(result['is_mock'])
        return result
    def test_success(self):
        r=self.run_response(httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'OK'}]},'finishReason':'STOP'}]}))
        self.assertTrue(r['generated_content_received']);self.assertTrue(r['reply_ok'])
    def test_404_array_redacted(self):
        r=self.run_response(httpx.Response(404,json=[{'error':{'code':404,'status':'NOT_FOUND','message':'test-secret token=other-private','details':[{'reason':'MODEL_UNAVAILABLE','metadata':{'key':'test-secret'}}]}}]))
        self.assertEqual(r['error']['google_status'],'NOT_FOUND');self.assertNotIn('test-secret',str(r));self.assertNotIn('other-private',str(r))
    def test_403_429_no_retry(self):
        for code,status in [(403,'PERMISSION_DENIED'),(429,'RESOURCE_EXHAUSTED')]:
            self.assertEqual(self.run_response(httpx.Response(code,json={'error':{'code':code,'status':status,'message':'denied'}}))['error']['google_code'],code)
    def test_non_json_no_raw_body(self):
        r=self.run_response(httpx.Response(404,text='test-secret private-response'))
        self.assertEqual(r['error'],{'http_status':404});self.assertNotIn('private-response',str(r))
    def test_empty_text_not_inference_success(self):
        r=self.run_response(httpx.Response(200,json={'candidates':[{'content':{'parts':[{'thought':True,'text':'internal'}]},'finishReason':'MAX_TOKENS'}]}))
        self.assertFalse(r['generated_content_received'])
    def test_timeout_one_request(self):
        calls=[]
        def handler(request):calls.append(request);raise httpx.ReadTimeout('test-secret')
        r=diagnose('test-secret',httpx.MockTransport(handler))
        self.assertEqual(r['status'],'timeout_stop');self.assertEqual(len(calls),1);self.assertNotIn('test-secret',str(r))

if __name__=='__main__':unittest.main()
