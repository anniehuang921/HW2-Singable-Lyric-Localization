"""User-run, one listModels call and at most one short completion. No retries."""
import getpass
import json
import os
from pathlib import Path
import re
import httpx
from .providers import CompatibleProvider, Settings, ProviderError, safe_http_error

BASE='https://generativelanguage.googleapis.com/v1beta/openai/'
MODEL='gemini-2.5-flash'
OUTPUT=Path(__file__).resolve().parents[1]/'docs/phase2b/gemini/minimal-diagnostic.json'

def main():
    # Never fall back to echoing stdin and never inspect another process's env.
    try:
        fd=os.open('/dev/tty',os.O_RDWR);os.close(fd)
    except OSError:
        print('請在 Remote SSH Terminal 互動執行；未發送 API 請求。');return
    key=getpass.getpass('Gemini Key（隱藏輸入，僅用於本次診斷）：')
    if not key:print('Key 為空，未發送請求。');return
    report={'requested_model':MODEL,'list_calls':0,'completion_calls':0,'real_api':True}
    try:
        with httpx.Client(timeout=30,follow_redirects=False,trust_env=False) as client:
            report['list_calls']=1
            response=client.get('https://generativelanguage.googleapis.com/v1beta/models',params={'pageSize':1000},headers={'x-goog-api-key':key})
        if response.status_code!=200:raise safe_http_error(response,key)
        body=response.json()
        models=[m for m in body.get('models',[]) if isinstance(m,dict)]
        names=[m.get('name','') for m in models if isinstance(m.get('name'),str) and re.fullmatch(r'models/[A-Za-z0-9._-]{1,120}',m['name'])]
        report['models']=names
        available=any(m.get('name')=='models/'+MODEL and 'generateContent' in m.get('supportedGenerationMethods',[]) for m in models)
        report['listed_generate_content_support']=available
        if not available:
            report['status']='requested_model_not_listed_stop' if not body.get('nextPageToken') else 'list_incomplete_stop'
        else:
            report['completion_calls']=1
            text=CompatibleProvider(Settings(BASE,MODEL,key,max_tokens=16)).generate('Reply only OK.')
            report['status']='short_completion_success'
            # Do not log arbitrary unfiltered model output in this diagnostic.
            report['reply_ok']=text.strip()=='OK'
    except ProviderError as exc:
        report['status']='api_error_stop';report['error']=exc.details or {'reason':str(exc)}
    except httpx.TimeoutException:report['status']='timeout_stop'
    except httpx.HTTPError:report['status']='connection_error_stop'
    except (ValueError,TypeError):report['status']='invalid_list_response_stop'
    finally:key=''
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open('w') as f:
        os.chmod(OUTPUT,0o600);json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print('診斷已停止；沒有更換模型、翻譯歌詞或啟用 Billing。')

if __name__=='__main__':main()
