"""Single authorized CSD experiment. Requires terminal-provided HW2 credentials."""
import json,os,shutil
from pathlib import Path
from datetime import datetime,timezone
from hw2_datasets.workflow import presenter,ExcerptController,ExcerptSinger,RID
from hw2_translation.providers import from_environment
OUT=Path('artifacts/phase4b');OUT.mkdir(parents=True,exist_ok=True,mode=0o700)

def main():
    if shutil.disk_usage('.').free<10*1024**3:raise RuntimeError('Local reserve below10GiB')
    from hw2_translation.credential_check import validate_key
    credential_check=validate_key()
    provider=from_environment()
    if provider.is_mock or provider.metadata()['model']!='gemini-3.5-flash-lite':raise RuntimeError('Wrong provider/model')
    p=presenter();record=ExcerptController(p,provider_factory=lambda:provider).translate(RID,print)
    from hw2_translation import providers
    result={'credential_check':credential_check,'request_count_this_execution':providers._REQUESTS,'recording_id':RID,'excerpt':p.excerpt,'comparison_path':record['artifact_path'],'modes':record['modes'],
            'provider':record['provider'],'comparison_request_count':sum(len(m['attempts']) for m in record['modes'].values()),
            'usage':{},'singing':{},'status':'translation_saved'}
    for mode in record['modes'].values():
        for attempt in mode['attempts']:
            for k,v in attempt.get('api_response',{}).get('usage',{}).items():result['usage'][k]=result['usage'].get(k,0)+v
    receipt=OUT/('experiment-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    def save():receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2));receipt.chmod(0o600)
    save()
    if record.get('errors') or any(not record['modes'].get(m,{}).get('segments') for m in ('direct','blt_assisted')):
        result['status']='translation_error_stop';result['errors']=record.get('errors',[]);save()
        from hw2_translation.providers import sanitize_message
        reasons='；'.join(sanitize_message(e.get('reason',''),provider.settings.api_key) for e in record.get('errors',[]))
        raise RuntimeError('Translation failed; stopped without retry. '+(reasons or 'Incomplete translation output')+' See private comparison.')
    singer=ExcerptSinger(p)
    for mode in ('blt_assisted','direct'):
        generated=singer.generate(RID,record,mode);result['singing'][mode]=generated;save()
        if generated['status']!='completed' or generated.get('is_mock'):
            result['status']='singing_error_stop';save();raise RuntimeError('Singing failed; stopped without retry. See private result.')
        duration=generated['audio_info']['duration_seconds'];source=(p.excerpt['frames']/p.excerpt['sample_rate'])
        if abs(duration-source)>2:result['status']='duration_mismatch_stop';save();raise RuntimeError('Singing duration differs from excerpt by >2s')
    result['status']='completed';save();print('兩份真實演唱完成；私人結果：'+str(receipt))

if __name__=='__main__':main()
