"""Optional local official-media UI integration; explicit no-audio mocks, no inference.
Run with PYTHONPATH=. and no service using port 7865.
"""
import json
from pathlib import Path
from unittest.mock import patch
import httpx
from gradio_client import Client
from hw2_ui.catalog import read_catalog,DEFAULT_ROOT
from hw2_ui.presenter import Presenter,AUDIO_CACHE
from hw2_ui.app import build_ui
from hw2_singing.adapter import SingingController,MockAdapter,NativeAdapter,OUTPUT
from hw2_translation.storage import DEFAULT_DIR
p=Presenter(read_catalog(),{'yingmusic_official':DEFAULT_ROOT});singer=SingingController(p,MockAdapter())
app=build_ui(p,saved_only=True,singing=True,singing_controller=singer)
rows=[]
try:
 app.launch(server_name='127.0.0.1',server_port=7865,share=False,prevent_thread_lock=True,quiet=True,allowed_paths=[str(AUDIO_CACHE),str(DEFAULT_DIR.resolve()),str(OUTPUT.resolve())])
 c=Client('http://127.0.0.1:7865',verbose=False,download_files=False,analytics_enabled=False)
 chosen=c.predict('SingEdit_EN_01',api_name='/select_demo');audio=httpx.get(chosen[2]['url']);assert audio.status_code==200
 c.predict('SingEdit_EN_01',api_name='/load_saved_translation')
 for mode in ['blt_assisted','direct','edited']:
  text=''
  if mode=='edited':text=c.predict('SingEdit_EN_01','blt_assisted',api_name='/load_candidate')+'呀'
  r=c.predict('SingEdit_EN_01',mode,text,api_name='/generate_singing')
  assert r[1]['is_mock'] is True and r[1]['status']=='mock_validated'
  assert r[2:5]==(None,None,None) or list(r[2:5])==[None,None,None]
  rows.append({'mode':mode,'status':r[1]['status'],'audio':None})
 singer.adapter=NativeAdapter(DEFAULT_ROOT)
 with patch.dict('os.environ',{'HW2_SINGING_ENABLED':'0'}):
  r=c.predict('SingEdit_EN_01','blt_assisted','',api_name='/generate_singing')
 assert r[1]['status']=='failed' and '未' in r[1]['error']
 stale=c.predict('SingEdit_EN_02','direct','',api_name='/generate_singing')
 assert stale[1]['status']=='failed'
 print(json.dumps({'mock_events':rows,'missing_models_error':r[1]['error'],'cross_demo_rejected':True,'original_audio_http':audio.status_code,'real_synthesis':False,'api_calls':0},ensure_ascii=False))
finally:app.close()
