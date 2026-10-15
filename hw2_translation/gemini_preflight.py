"""Exactly one authorized short test, before the UI inherits its key."""
import datetime
import json
import os
from pathlib import Path
from .providers import from_environment,ProviderError,sanitize_message

def reply_is_ok(text):
    return isinstance(text,str) and text.strip() in ('OK','OK.')

def main():
    provider=from_environment()
    if provider.settings.model!='gemini-3.5-flash-lite' or provider.settings.base_url!='https://generativelanguage.googleapis.com/v1beta/openai/':
        raise SystemExit('不是本輪授權的 Gemini 設定，未發送請求')
    if not provider.settings.api_key:raise SystemExit('Key 未設定，未發送請求')
    record={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provider':provider.metadata(),'request_count':1,'is_mock':False}
    try:
        text=provider.generate('Reply with OK.')
        record['api_response']=provider.last_response
        returned=provider.last_response.get('response_model','')
        record['model_confirmed']=returned=='gemini-3.5-flash-lite' or returned.startswith('gemini-3.5-flash-lite-')
        record['generated_content_received']=True
        record['safe_reply']=sanitize_message(text,provider.settings.api_key)[:80]
        record['reply_ok']=reply_is_ok(text)
        record['status']='passed' if record['model_confirmed'] and record['reply_ok'] else 'response_mismatch_stop'
    except ProviderError as exc:
        record['status']='api_error_stop';record['error']=exc.details or {'reason':str(exc)}
    folder=Path(__file__).resolve().parents[1]/'artifacts/gemini'
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    path=folder/('flash35lite-preflight-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'.json')
    with path.open('x') as f:
        os.chmod(path,0o600);json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    if record['status']=='passed':
        evidence=folder/'preflight.json'
        with evidence.open('w') as f:
            os.chmod(evidence,0o600);json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(record,ensure_ascii=False,indent=2))
    print('短測結果已保存：',path.name)
    if record['status']!='passed':raise SystemExit('短測未通過；已停止，不啟動翻譯 UI。請回報結果。')

if __name__=='__main__':main()
