"""Independent one-request native Gemini diagnostic. No translation imports/calls."""
import datetime
import getpass
import json
import os
from pathlib import Path
import re
import httpx
from .providers import sanitize_message

URL='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
OUTPUT=Path(__file__).resolve().parents[1]/'docs/phase2b/gemini/native-diagnostic.json'

def safe_error(response,key):
    result={'http_status':response.status_code}
    try:
        if len(response.content)>16384:return result
        body=response.json()
        # Some gateways wrap the Google error object in a JSON array.
        objects=body[:3] if isinstance(body,list) else [body]
        error=next((x['error'] for x in objects if isinstance(x,dict) and isinstance(x.get('error'),dict)),{})
        code=error.get('code')
        if isinstance(code,int) and not isinstance(code,bool):result['google_code']=code
        status=error.get('status')
        if isinstance(status,str) and re.fullmatch(r'[A-Z_]{1,40}',status):result['google_status']=sanitize_message(status,key)
        message=sanitize_message(error.get('message'),key)
        if message:result['google_message']=message
        details=error.get('details')
        if isinstance(details,list):
            filtered=[]
            for item in details[:3]:
                if not isinstance(item,dict):continue
                row={name:sanitize_message(item[name],key) for name in ('@type','reason','domain','retryDelay') if isinstance(item.get(name),str)}
                if row:filtered.append(row)
            if filtered:result['google_details']=filtered
    except (ValueError,TypeError):pass
    return result

def diagnose(key,transport=None):
    report={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'model':'gemini-2.5-flash','endpoint':URL,'request_limit':1,'request_count':0,
            'max_output_tokens':16,'timeout_seconds':30,'is_mock':transport is not None}
    try:
        with httpx.Client(timeout=30,follow_redirects=False,trust_env=False,transport=transport) as client:
            report['request_count']=1
            response=client.post(URL,headers={'x-goog-api-key':key},json={
                'contents':[{'role':'user','parts':[{'text':'Reply with OK.'}]}],
                'generationConfig':{'maxOutputTokens':16}})
        report['http_status']=response.status_code
        if response.status_code!=200:
            report['status']='api_error_stop';report['error']=safe_error(response,key)
            return report
        if len(response.content)>16384:raise ValueError()
        body=response.json();texts=[];finishes=[]
        for candidate in body.get('candidates',[])[:3]:
            if not isinstance(candidate,dict):continue
            finish=candidate.get('finishReason')
            if isinstance(finish,str):finishes.append(sanitize_message(finish,key))
            for part in candidate.get('content',{}).get('parts',[]):
                if isinstance(part,dict) and not part.get('thought') and isinstance(part.get('text'),str):texts.append(part['text'])
        text=''.join(texts).strip()
        report.update(status='generated_content_received' if text else 'http_200_without_text',
                      generated_content_received=bool(text),reply_ok=text=='OK',
                      safe_text_preview=sanitize_message(text,key)[:80],finish_reasons=finishes)
    except httpx.TimeoutException:report['status']='timeout_stop'
    except httpx.HTTPError:report['status']='connection_error_stop'
    except (ValueError,TypeError,AttributeError):report['status']='invalid_response_stop'
    return report

def main():
    try:fd=os.open('/dev/tty',os.O_RDWR);os.close(fd)
    except OSError:
        print('請在 Remote SSH 互動終端執行；未發送請求。');return
    key=getpass.getpass('請輸入相同 Tech HW2 Gemini Key（隱藏輸入）：')
    if not key:print('Key 為空；未發送請求。');return
    try:report=diagnose(key)
    finally:key=''
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open('w') as f:
        os.chmod(OUTPUT,0o600);json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print('單次 Native 診斷已結束，不重試、不查模型清單、不翻譯或變更 Billing。')

if __name__=='__main__':main()
