"""Optional real-media CSD excerpt/replay UI test; never invokes API/GPU."""
import io,json
from pathlib import Path
import httpx,soundfile as sf
from gradio_client import Client
from hw2_datasets.workflow import presenter,ExcerptController,ExcerptSinger,RID
from hw2_datasets.excerpt import ROOT
from hw2_ui.app import build_ui
from hw2_ui.presenter import AUDIO_CACHE
from hw2_singing.adapter import OUTPUT
from hw2_translation.storage import DEFAULT_DIR
p=presenter()
def forbidden(*args,**kwargs):raise AssertionError('No real API/GPU calls in live test')
singer=ExcerptSinger(p);singer.generate=forbidden
app=build_ui(p,ExcerptController(p,provider_factory=forbidden),saved_only=True,singing=True,singing_controller=singer)
try:
 app.launch(server_name='127.0.0.1',server_port=7865,share=False,prevent_thread_lock=True,quiet=True,
  allowed_paths=[str(ROOT),str(AUDIO_CACHE),str(OUTPUT.resolve()),str(DEFAULT_DIR.resolve())])
 c=Client('http://127.0.0.1:7865',verbose=False,download_files=False,analytics_enabled=False)
 c.predict('csd','en','en','全部',api_name='/select_source');c.predict('en','CSD_en042',api_name='/csd_song')
 original=c.predict(RID,api_name='/select_demo');clip=c.predict(RID,api_name='/verified_excerpt')
 assert clip[0]=='\n'.join(p.excerpt['segments']) and original[1]==p.csd.recordings[RID].lyrics
 audio=httpx.get(clip[1]['url']);assert audio.status_code==200
 samples,rate=sf.read(io.BytesIO(audio.content));assert len(samples)==p.excerpt['frames'] and rate==44100
 assert httpx.get(original[2]['url']).status_code==200
 report={'excerpt_http':200,'full_original_http':200,'excerpt_seconds':len(samples)/rate,'saved_csd_results':False,'new_api_calls':0,'new_gpu_inference':0}
 try:record=ExcerptController(p).load_saved(RID)
 except ValueError:pass
 else:
  c.predict(RID,api_name='/load_saved_translation')
  for mode in ['blt_assisted','direct']:
   result=c.predict(RID,mode,'',api_name='/load_saved_singing');assert result[1]['status']=='completed' and result[1]['is_mock'] is False
   assert httpx.get(result[3 if mode=='blt_assisted' else 2]['url']).status_code==200
  report['saved_csd_results']=True
 c.predict('yingmusic_official','en','en','全部',api_name='/select_source');c.predict('SingEdit_EN_01',api_name='/load_saved_translation')
 old=c.predict('SingEdit_EN_01','blt_assisted','',api_name='/load_saved_singing');assert old[1]['status']=='completed'
 assert httpx.get(old[3]['url']).status_code==200;report['old_en01_replay_http']=200
 Path('artifacts/phase4b').mkdir(exist_ok=True);Path('artifacts/phase4b/ui-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
finally:app.close()
