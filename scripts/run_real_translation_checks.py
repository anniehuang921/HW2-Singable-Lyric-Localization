"""Authorized UI experiment: at most two comparisons, no provider/key access."""
import io
import json
from pathlib import Path
import httpx
import soundfile as sf
from gradio_client import Client

OUT=Path('docs/phase2b/gemini/real35lite')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    client=Client('http://127.0.0.1:7863',verbose=False,download_files=False,analytics_enabled=False)
    summaries=[]
    for name in ['SingEdit_EN_01','SingEdit_EN_02']:
        selected=client.predict(name,api_name='/select_demo')
        audio=httpx.get(selected[2]['url'],timeout=20);audio.raise_for_status()
        samples,rate=sf.read(io.BytesIO(audio.content))
        result=client.predict(name,api_name='/translate')
        (OUT/(name+'-ui.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        if not result[5]:
            print('STOP: UI did not produce a comparison artifact:',result[0]);break
        saved=httpx.get(result[5]['url'],timeout=20);saved.raise_for_status();record=saved.json()
        (OUT/(name+'-comparison.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        assert record['is_mock'] is False
        assert record['provider']['model']=='gemini-3.5-flash-lite'
        summary={'demo_id':name,'provider':record['provider'],'errors':record['errors'],
                 'audio_http':audio.status_code,'decoded_audio_frames':len(samples),'sample_rate':rate,'modes':{}}
        for mode,item in record['modes'].items():
            summary['modes'][mode]={k:item.get(k) for k in ['segments','status','revisions','validation','error']}
            summary['modes'][mode]['responses']=[a.get('api_response',{}) for a in item['attempts']]
        summaries.append(summary)
        print(json.dumps(summary,ensure_ascii=False),flush=True)
        if record['errors'] or any(not item.get('segments') for item in record['modes'].values()):
            print('STOP on failure; no next demo or retry',flush=True);break
        for mode in ['direct','blt_assisted']:
            candidate=client.predict(name,mode,api_name='/load_candidate')
            assert candidate.splitlines()==record['modes'][mode]['segments']
            # A deterministic automated editing test, not a human quality judgement.
            edited=candidate.splitlines();edited[0]+='呀'
            edit=client.predict(name,mode,'\n'.join(edited),api_name='/validate_edit')
            assert edit[0]['before']==record['modes'][mode]['segments'] and edit[0]['after']==edited
            (OUT/(name+'-'+mode+'-automated-edit.json')).write_text(json.dumps(edit[0],ensure_ascii=False,indent=2)+'\n')
        summary['candidate_edit_and_original_blt_revalidation']='PASS (automated, no LLM calls)'
    (OUT/'summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
