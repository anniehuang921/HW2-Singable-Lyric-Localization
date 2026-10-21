"""Offline credential handoff checks. Never return the credential or its hash."""
import os

def validate_key(value=None):
    value=os.environ.get('HW2_LLM_API_KEY','') if value is None else value
    if not isinstance(value,str) or not value:
        raise ValueError('HW2_LLM_API_KEY 未傳入 Python，未發出 API 請求')
    if value!=value.strip() or any(c.isspace() for c in value):
        raise ValueError('API Key 含空白／換行；請只貼入 Key 本身，未發出 API 請求')
    if value.startswith(('"',"'")) or value.endswith(('"',"'")):
        raise ValueError('API Key 含外層引號；請只貼入 Key 本身，未發出 API 請求')
    return {'key_received_by_python':True,'input_checks_passed':True,
            'validity_verified_with_google':False}

if __name__=='__main__':
    try:validate_key()
    except ValueError as exc:raise SystemExit(str(exc)) from None
    print('Python 已取得非空 Key，離線輸入檢查通過；尚未驗證 Google 有效性。')
