"""JSON subprocess bridge to the isolated, unmodified original BLT APIs."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_PYTHON=str(Path.home()/'.conda/envs/hw2-blt/bin/python')
WARNINGS=[
 '原版中文押韻未去除尾端標點。',
 '原版 validator 行數不一致時 feedback 可能與 syllables_match 矛盾；以旗標與實際行數為準。',
 '這是遵循 Skill 規則的移植編排，不是 Claude Code 原版 Agent 重現。',
 '音節／押韻符合不代表翻譯品質或可唱性通過。']

class Bridge:
    def __init__(self, python=None):self.python=python or os.getenv('HW2_BLT_PYTHON',DEFAULT_PYTHON)
    def call(self, action, source, target=None):
        env=os.environ.copy(); env['PYTHONPATH']=str(ROOT/'src'); env['PYTHONDONTWRITEBYTECODE']='1'
        env.pop('HW2_LLM_API_KEY', None)  # BLT tools do not need the LLM credential.
        try:
            p=subprocess.run([self.python,str(Path(__file__).resolve()),'--worker'],input=json.dumps({'action':action,'source':source,'target':target}),text=True,capture_output=True,timeout=45,env=env)
        except (OSError,subprocess.TimeoutExpired):raise RuntimeError('BLT 環境不存在或工具逾時') from None
        if p.returncode:raise RuntimeError('BLT 原版工具失敗；請檢查 hw2-blt 環境')
        result=json.loads(p.stdout)
        result['tool_stderr']=p.stderr
        return result
    def analyze(self,source):return self.call('analyze',source)
    def validate(self,source,target):return self.call('validate',source,target)

def worker():
    from blt_skills import count_syllables,detect_rhyme_scheme,get_syllable_patterns,verify_all_constraints
    payload=json.load(sys.stdin); source=payload['source']
    constraints={'target_syllables':[count_syllables(s,'en-us') for s in source],
                 'rhyme_scheme':detect_rhyme_scheme(source,'en-us'),
                 'target_patterns':get_syllable_patterns(source,'en-us')}
    if payload['action']=='analyze':result=constraints
    else:
        target=payload['target']
        result=verify_all_constraints(target,'cmn',**constraints)
        result['constraints']=constraints
        result['segment_count_match']=len(target)==len(source)
        import re
        result['han_only']=all(bool(s) and re.fullmatch(r'[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]+',s) is not None for s in target)
        result['warnings']=WARNINGS
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':worker()
