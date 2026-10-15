"""Offline validation of the already successful test. Never calls a provider."""
import json
import os
from pathlib import Path
from .gemini_preflight import reply_is_ok

EVIDENCE=Path(os.environ.get('HW2_PREFLIGHT_EVIDENCE', Path(__file__).resolve().parents[1]/'artifacts/gemini/preflight.json'))

def verify(record):
    provider=record.get('provider',{});response=record.get('api_response',{})
    expected={'model':'gemini-3.5-flash-lite',
              'base_url':'https://generativelanguage.googleapis.com/v1beta/openai/',
              'temperature':0.2,'max_tokens':4096,'timeout':45,'reasoning_effort':'low'}
    valid=(record.get('is_mock') is False and provider.get('is_mock') is False
           and record.get('request_count')==1 and response.get('http_status')==200
           and response.get('response_model')=='gemini-3.5-flash-lite'
           and record.get('model_confirmed') is True and record.get('generated_content_received') is True
           and reply_is_ok(record.get('safe_reply'))
           and all(provider.get(k)==v for k,v in expected.items()))
    if not valid:raise ValueError('既有短測紀錄不符本輪模型／成功／參數要求，未啟動；不會補發API短測')

if __name__=='__main__':
    try:verify(json.loads(EVIDENCE.read_text()))
    except (ValueError,OSError,TypeError):raise SystemExit('無法核對既有成功短測；停止且不發API')
    print('已在本機核對既有 HTTP200／OK. 短測；沒有發送新請求。')
