"""Bounded comparison pipeline and segment-preserving experiment records."""
import datetime
import json
import re
from opencc import OpenCC
from .providers import ProviderError

CONVERTER=OpenCC('s2t')

def parse_output(raw,ids):
    try:
        text=raw.strip()
        if text.startswith('```'):text=re.sub(r'^```(?:json)?\s*|\s*```$','',text)
        rows=json.loads(text)['segments']
        if not isinstance(rows,list) or [r['id'] for r in rows]!=ids:raise ValueError()
        lines=[r['text'] for r in rows]
        if any(not isinstance(s,str) or not s.strip() or '\n' in s or '|' in s for s in lines):raise ValueError()
        return [CONVERTER.convert(s.strip()) for s in lines]
    except (ValueError,KeyError,TypeError):raise ProviderError('模型輸出不是完整、依序且同 ID 的 segments JSON；未重試格式錯誤') from None

def satisfied(v):
    return all(v.get(k,False) for k in ['syllables_match','rhymes_valid','segment_count_match','han_only'])

def score(v):
    actual=v['syllables']; target=v['constraints']['target_syllables']
    return (not v['segment_count_match'],not v['han_only'],sum(abs(a-b) for a,b in zip(actual,target)),not v['rhymes_valid'])

class Engine:
    def __init__(self,provider,bridge,max_revisions=2):
        if not 0<=max_revisions<=2:raise ValueError('最多兩次修訂')
        self.provider=provider;self.bridge=bridge;self.max_revisions=max_revisions
    def run(self,demo,progress=lambda message:None):
        if demo.language!='en' or not demo.original_segments:raise ProviderError('僅接受原詞完整的英文 Demo')
        source=demo.original_segments;ids=[f'{demo.id}:{i+1:03d}' for i in range(len(source))]
        record={'demo_id':demo.id,'segment_ids':ids,'source':source,'source_revision':demo.source_revision,
                'provider':self.provider.metadata(),'is_mock':self.provider.is_mock,
                'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'implementation':'Skill-rule port using original BLT APIs; not original agent',
                'modes':{},'errors':[],'call_limit':2+self.max_revisions,
                'blt_core_head':'0591aa254c4c26093e3acc54f1dbffe7e71e0078',
                'traditional_conversion':'OpenCC s2t; raw output retained',
                'refinement_policy':'最多 2 次整批修訂；不完整重現原 Skill 每行 10 次與 pattern 15% 改善閾值'}
        base='將以下英文歌詞翻譯為自然的繁體中文，保留意思、情緒、意象與逐段對應。只輸出 JSON：'+json.dumps({'segments':[{'id':i,'text':'中文歌詞'} for i in ids]},ensure_ascii=False)+'\n原文：'+json.dumps(list(zip(ids,source)),ensure_ascii=False)
        # Direct generation precedes extraction and receives no musical constraints.
        for mode in ['direct','blt_assisted']:
            progress('生成 '+mode)
            mode_record={'attempts':[],'status':'running'};record['modes'][mode]=mode_record
            try:
                constraints=self.bridge.analyze(source) if mode=='blt_assisted' else None
                prompt=base
                if constraints:
                    prompt+='\n遵循原 BLT lyrics-translator Skill：每段漢字數精確等於目標音節；同韻組須押韻、不同組不得押韻；盡量接近字詞音節 pattern。只使用漢字，不含數字、Latin 或標點。限制：'+json.dumps(constraints,ensure_ascii=False)
                iterations=1+self.max_revisions if constraints else 1
                best=None
                for index in range(iterations):
                    if index:progress(f'BLT 有限修訂 {index}/{self.max_revisions}')
                    attempt={'prompt':prompt,'revision':index};mode_record['attempts'].append(attempt)
                    raw=self.provider.generate(prompt);attempt['raw_output']=raw
                    attempt['api_response']=dict(getattr(self.provider,'last_response',{}))
                    lines=parse_output(raw,ids);attempt['segments']=lines
                    verification=self.bridge.validate(source,lines);attempt['validation']=verification
                    if best is None or score(verification)<score(best['validation']):best=attempt
                    mode_record['segments']=best['segments'];mode_record['validation']=best['validation']
                    if not constraints or satisfied(verification):break
                    prompt=base+'\n只使用漢字。依原 BLT feedback 修改翻譯，保留各段 ID／意思，優先字詞 pattern、精確音節，其次押韻。限制：'+json.dumps(constraints,ensure_ascii=False)+'\n前版：'+json.dumps(lines,ensure_ascii=False)+'\n實際驗證：'+json.dumps(verification,ensure_ascii=False)
                mode_record['revisions']=max(0,len(mode_record['attempts'])-1)
                mode_record['status']='completed' if mode=='direct' or satisfied(mode_record['validation']) else 'revision_limit_reached'
            except (ProviderError,RuntimeError) as exc:
                if mode_record['attempts']:
                    mode_record['attempts'][-1]['api_response']=dict(getattr(self.provider,'last_response',{}))
                mode_record['revisions']=max(0,len(mode_record['attempts'])-1)
                mode_record['status']='failed';mode_record['error']=str(exc);record['errors'].append({'mode':mode,'reason':str(exc)})
                # No second generation after a provider/tool failure: cap expenses.
                break
        return record
