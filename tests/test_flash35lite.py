import json
import unittest
from pathlib import Path
import httpx
from hw2_translation.providers import CompatibleProvider,Settings

class FlashLiteTests(unittest.TestCase):
    def test_model_settings_and_response(self):
        def handler(request):
            payload=json.loads(request.content)
            self.assertEqual(payload['model'],'gemini-3.5-flash-lite')
            self.assertEqual(payload['reasoning_effort'],'low')
            self.assertEqual(payload['max_tokens'],4096)
            return httpx.Response(200,json={'model':'gemini-3.5-flash-lite','usage':{'total_tokens':12},'choices':[{'message':{'content':'OK'},'finish_reason':'stop'}]})
        provider=CompatibleProvider(Settings('https://generativelanguage.googleapis.com/v1beta/openai/','gemini-3.5-flash-lite',max_tokens=4096,timeout=45,reasoning_effort='low'),httpx.MockTransport(handler))
        self.assertEqual(provider.generate('Reply with OK.'),'OK')
        self.assertEqual(provider.last_response['response_model'],'gemini-3.5-flash-lite')
    def test_startup_and_preflight_pinned(self):
        root=Path(__file__).resolve().parents[1]
        for name in ['scripts/start_gemini_ui.sh','hw2_translation/gemini_preflight.py']:
            text=(root/name).read_text()
            self.assertIn('gemini-3.5-flash-lite',text)
            self.assertNotIn('gemini-3.8-flash',text)
        self.assertIn('flash35lite-preflight-',(root/'hw2_translation/gemini_preflight.py').read_text())

class PreflightReplyTests(unittest.TestCase):
    def test_only_short_ok_variants(self):
        from hw2_translation.gemini_preflight import reply_is_ok
        for text in ['OK','OK.',' OK.\n']:self.assertTrue(reply_is_ok(text))
        for text in ['','Okay','OK but no','Not OK','OK..',None]:self.assertFalse(reply_is_ok(text))
