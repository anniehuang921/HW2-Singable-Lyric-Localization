"""Optional real local CSD/media HTTP event checks; zero API calls/inference."""
import io
import json
from pathlib import Path
import httpx
import soundfile as sf
from gradio_client import Client
from hw2_ui.catalog import DEFAULT_ROOT,read_catalog
from hw2_ui.presenter import AUDIO_CACHE
from hw2_datasets.csd import CSD
from hw2_datasets.presenter import DatasetPresenter
from hw2_ui.app import build_ui
from hw2_translation.controller import Controller
from hw2_translation.storage import DEFAULT_DIR
from hw2_singing.adapter import SingingController,OUTPUT

p=DatasetPresenter(read_catalog(),{'yingmusic_official':DEFAULT_ROOT},CSD())
def disabled():raise AssertionError('Phase 4A must not call LLM')
singer=SingingController(p)
def forbidden(*args,**kwargs):raise AssertionError('Phase 4A must not synthesize')
singer.generate=forbidden
app=build_ui(p,Controller(p,provider_factory=disabled),saved_only=True,singing=True,singing_controller=singer)
rows=[]
try:
 app.launch(server_name='127.0.0.1',server_port=7865,share=False,prevent_thread_lock=True,quiet=True,
            allowed_paths=[str(AUDIO_CACHE),str(DEFAULT_DIR.resolve()),str(OUTPUT.resolve())])
 c=Client('http://127.0.0.1:7865',verbose=False,download_files=False,analytics_enabled=False)
 c.predict('csd','en','en','全部',api_name='/select_source')
 for language,song in [('en','CSD_en042'),('ko','CSD_kr001')]:
  c.predict(language,None,api_name='/csd_language')
  result=c.predict(language,song,api_name='/csd_song')
  variants=p.csd.variants(song)
  for _,rid in variants:
   selected=c.predict(rid,api_name='/select_demo')
   assert selected[1]==p.csd.recordings[rid].lyrics
   assert selected[6]['song_id']==song and selected[6]['recording_id']==rid
   response=httpx.get(selected[2]['url']);assert response.status_code==200
   samples,rate=sf.read(io.BytesIO(response.content));assert rate==44100 and len(samples)>0
   partial=httpx.get(selected[2]['url'],headers={'Range':'bytes=0-4095'});assert partial.status_code==206
   rows.append({'recording_id':rid,'http':200,'range_http':206,'frames':len(samples)})
 # Restore the English dropdown choices before invoking its guarded endpoints.
 c.predict('en',None,api_name='/csd_language')
 c.predict('en','CSD_en042',api_name='/csd_song')
 # Defense-in-depth: direct invocation cannot trigger CSD translation/singing.
 blocked=c.predict('CSD_en042a',api_name='/translate');assert 'Phase 4A' in blocked[0]
 blocked=c.predict('CSD_en042a','blt_assisted','',api_name='/generate_singing');assert 'Phase 4A' in blocked[1]['error']
 c.predict('yingmusic_official','en','en','全部',api_name='/select_source')
 original=c.predict('SingEdit_EN_01',api_name='/select_demo');assert httpx.get(original[2]['url']).status_code==200
 saved=c.predict('SingEdit_EN_01',api_name='/load_saved_translation');assert saved[1] and saved[2]
 sung=c.predict('SingEdit_EN_01','blt_assisted','',api_name='/load_saved_singing')
 assert sung[1]['status']=='completed' and sung[1]['is_mock'] is False
 assert httpx.get(sung[3]['url']).status_code==200
 result={'csd_playback':rows,'official_original_http':200,'saved_translation_loaded':True,'saved_singing_http':200,'new_api_calls':0,'new_synthesis':0}
 Path('artifacts/datasets/csd/ui-event-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:app.close()
