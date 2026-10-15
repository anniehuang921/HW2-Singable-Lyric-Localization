"""Original synthetic inputs only; not measured Gemini translations or official lyrics."""
from dataclasses import replace
from pathlib import Path
import tempfile
import numpy as np
import soundfile as sf
from hw2_ui.catalog import Demo

_TEMP = tempfile.TemporaryDirectory(prefix='hw2-synthetic-')
ROOT = Path(_TEMP.name)
sf.write(ROOT/'reference.wav', np.sin(np.arange(4800)*0.1)*0.1, 48000)
sf.write(ROOT/'melody.wav', np.sin(np.arange(4800)*0.2)*0.1, 48000)

def read_catalog():
    demos=[]
    for lang in ['en','zh']:
        for i,source in [(1,['Silver lantern in the rain','Quiet rivers flow']),(2,['Clouds drift over trees','Softly now','Bright stars shine above','Dream on'])]:
            if lang=='zh': source=['測試春風','測試天空']
            d=Demo(f'SingEdit_{lang.upper()}_{i:02d}','Synthetic fixture',lang,'Lyric Editing','yingmusic_official','https://example.test/synthetic','synthetic','generated test fixture',source,'synthetic association','reference.wav','reference.wav','reference.wav','|'.join(source),'合成目標',['Synthetic; not official material'])
            demos.append(d)
            demos.append(replace(d,id=f'melody_control_{lang.upper()}_{i:02d}',task='Melody Control',original_segments=None,original_audio='melody.wav',melody_audio='melody.wav'))
    return demos

def success_evidence():
    """Schema fixture, never evidence of a real request."""
    return {'provider':{'model':'gemini-3.5-flash-lite','base_url':'https://generativelanguage.googleapis.com/v1beta/openai/','temperature':0.2,'max_tokens':4096,'timeout':45,'reasoning_effort':'low','is_mock':False},'request_count':1,'is_mock':False,'api_response':{'http_status':200,'response_model':'gemini-3.5-flash-lite'},'model_confirmed':True,'generated_content_received':True,'safe_reply':'OK.'}

def comparison():
    d=read_catalog()[0]
    return {'demo_id':d.id,'source':d.original_segments,'segment_ids':[f'{d.id}:001',f'{d.id}:002'],'is_mock':False,'provider':{'model':'gemini-3.5-flash-lite'},'modes':{'direct':{'segments':['合成文字','測試文字']},'blt_assisted':{'segments':['合成文字','測試文字']}}}
