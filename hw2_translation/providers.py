"""Explicitly authorized replaceable providers. Never use ambient Codex keys."""
from dataclasses import dataclass, field
import os
import json
import re
import threading
from urllib.parse import quote, quote_plus
from urllib.parse import urlsplit
import httpx

class ProviderError(RuntimeError):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}

def completion_url(base):
    return base.rstrip('/') + '/chat/completions'

def sanitize_message(value, secret=''):
    if not isinstance(value, str):return ''
    # Scrub before truncation so a long/encoded secret is never partially logged.
    for token in {secret, quote(secret, safe=''), quote_plus(secret)} - {''}:
        value = value.replace(token, '[REDACTED]')
    value = re.sub(r'(?i)authorization[^\r\n]*', '[REDACTED HEADER]', value)
    value = re.sub(r'(?i)bearer\s+\S+|(?:api[_-]?key|key|token|secret)\s*[=:]\s*[^\s&,]+', '[REDACTED]', value)
    value = re.sub(r'https?://[^/\s:@]+:[^/\s@]+@', 'https://[REDACTED]@', value)
    value = re.sub(r'[A-Za-z0-9_+/%=-]{24,}', '[REDACTED TOKEN]', value)
    value = ''.join(c if c.isprintable() else ' ' for c in value)
    return value[:400]

def safe_http_error(response, secret=''):
    details = {'http_status': response.status_code}
    try:
        if len(response.content)>16384:raise ValueError()
        body=response.json()
        objects=body[:3] if isinstance(body,list) else [body]
        error=next((x['error'] for x in objects if isinstance(x,dict) and isinstance(x.get('error'),dict)),{})
        if isinstance(error,dict):
            status=error.get('status')
            if isinstance(status,str) and re.fullmatch(r'[A-Z_]{1,40}',status):details['google_status']=sanitize_message(status,secret)
            code=error.get('code')
            if isinstance(code,int) and not isinstance(code,bool):details['google_code']=code
            message=sanitize_message(error.get('message'),secret)
            if message:details['google_message']=message
    except (ValueError,TypeError):pass
    return ProviderError('LLM HTTP 錯誤；未自動重試：'+json.dumps(details,ensure_ascii=False),details)


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    api_key: str = field(default='', repr=False)
    temperature: float = 0.2
    max_tokens: int = 1024
    timeout: float = 30.0
    reasoning_effort: str | None = None

_BUDGET_LOCK=threading.Lock()
_REQUESTS=0
_HALTED=False

def reserve_request():
    global _REQUESTS
    limit=os.getenv('HW2_LLM_REQUEST_LIMIT')
    if limit is None:return
    with _BUDGET_LOCK:
        if _HALTED:raise ProviderError('本輪已遇到 API／回應錯誤，禁止後續請求；請先回報')
        if _REQUESTS>=int(limit):raise ProviderError('本轮請求上限已達，未發送新請求')
        _REQUESTS+=1

def halt_requests():
    global _HALTED
    if os.getenv('HW2_LLM_REQUEST_LIMIT') is not None:
        with _BUDGET_LOCK:_HALTED=True

class CompatibleProvider:
    is_mock = False
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self.last_response = {}
    def metadata(self):
        s = self.settings
        return dict(provider='openai-compatible', model=s.model, base_url=s.base_url,
                    temperature=s.temperature, max_tokens=s.max_tokens, timeout=s.timeout, reasoning_effort=s.reasoning_effort, is_mock=False)
    def generate(self, prompt):
        s = self.settings
        reserve_request()
        payload={'model':s.model,'messages':[{'role':'user','content':prompt}],
                 'temperature':s.temperature,'max_tokens':s.max_tokens}
        if s.reasoning_effort:payload['reasoning_effort']=s.reasoning_effort
        headers = {'Authorization': 'Bearer ' + s.api_key} if s.api_key else {}
        try:
            with httpx.Client(timeout=s.timeout, transport=self.transport, follow_redirects=False, trust_env=False) as c:
                r=c.post(completion_url(s.base_url), headers=headers,
                         json=payload)
            self.last_response={'http_status':r.status_code}
            if r.status_code != 200:
                halt_requests()
                raise safe_http_error(r, s.api_key)
            body=r.json()
            response_model=body.get('model')
            if isinstance(response_model,str):self.last_response['response_model']=sanitize_message(response_model,s.api_key)
            usage=body.get('usage',{})
            if isinstance(usage,dict):
                self.last_response['usage']={k:v for k,v in usage.items() if k in ('prompt_tokens','completion_tokens','total_tokens') and isinstance(v,int) and not isinstance(v,bool)}
            finish=body['choices'][0].get('finish_reason')
            if isinstance(finish,str):self.last_response['finish_reason']=sanitize_message(finish,s.api_key)
            text = body['choices'][0]['message']['content']
            if not isinstance(text, str) or not text.strip():
                raise ValueError()
            if s.api_key and s.api_key in text:raise ValueError()
            return text
        except httpx.TimeoutException:
            halt_requests()
            raise ProviderError('LLM 請求逾時；未自動重試') from None
        except httpx.HTTPError:
            halt_requests()
            raise ProviderError('LLM 連線失敗；未自動重試') from None
        except (KeyError, IndexError, TypeError, ValueError):
            halt_requests()
            raise ProviderError('LLM 回應格式無效') from None

class MockProvider:
    is_mock = True
    def __init__(self, responses):
        self.responses = iter(responses); self.prompts=[]
    def metadata(self):
        return {'provider':'mock','model':'mock-fixture','is_mock':True}
    def generate(self,prompt):
        self.prompts.append(prompt)
        try:return next(self.responses)
        except StopIteration:raise ProviderError('mock fixture exhausted') from None

def from_environment():
    if os.getenv('HW2_LLM_AUTHORIZED') != '1':
        raise ProviderError('尚未配置已授權 LLM；需明確設定 HW2_LLM_AUTHORIZED=1、HW2_LLM_BASE_URL、HW2_LLM_MODEL')
    base=os.getenv('HW2_LLM_BASE_URL',''); model=os.getenv('HW2_LLM_MODEL','')
    url=urlsplit(base)
    if not model or url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ProviderError('LLM 模型或 endpoint 設定無效；URL 不得含憑證或 query')
    if url.scheme=='http' and url.hostname not in ('localhost','127.0.0.1','::1'):
        raise ProviderError('遠端 LLM endpoint 需使用 HTTPS')
    effort=os.getenv('HW2_LLM_REASONING_EFFORT') or None
    if effort not in (None,'minimal','low','medium','high'):raise ProviderError('reasoning_effort 設定無效')
    max_tokens=int(os.getenv('HW2_LLM_MAX_TOKENS','1024'))
    timeout=float(os.getenv('HW2_LLM_TIMEOUT','30'))
    if not 1<=max_tokens<=4096 or not 1<=timeout<=60:raise ProviderError('生成上限／Timeout 超出本專案範圍')
    limit=os.getenv('HW2_LLM_REQUEST_LIMIT')
    if limit is not None and (not limit.isdigit() or not 1<=int(limit)<=9):raise ProviderError('請求上限設定無效')
    return CompatibleProvider(Settings(base,model,os.getenv('HW2_LLM_API_KEY',''),max_tokens=max_tokens,timeout=timeout,reasoning_effort=effort))
