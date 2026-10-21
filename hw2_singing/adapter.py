"""Prepare auditable requests; no torch or YingMusic imports in the UI process."""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
import numpy as np
import soundfile as sf
from opencc import OpenCC
from hw2_ui.catalog import availability, safe_asset

OUTPUT = Path(__file__).resolve().parents[1] / 'artifacts/singing'
MODEL_ID = 'ASLP-lab/YingMusic-Singer-Plus'
REQUIRED = ('model_cfg_path','ckpt_path','vae_config_path','vae_ckpt_path','midi_teacher_ckpt_path')

@dataclass(frozen=True)
class Settings:
    seed: int = 666
    nfe_step: int = 32
    cfg_strength: float = 3.0
    t_shift: float = 0.5
    sil_len_to_end: float = 0.5
    simplify: bool = True
    separate_vocals: bool = True
    mix_accompaniment: bool = True

    def validate(self):
        if not isinstance(self.seed,int) or not 0 <= self.seed < 2**31:raise ValueError('Seed須為固定非負整數')
        if not 1 <= self.nfe_step <= 64 or not 0 <= self.cfg_strength <= 10:raise ValueError('推論步數或CFG超出限制')
        if not 0 <= self.t_shift <= 1 or not 0 <= self.sil_len_to_end <= 2:raise ValueError('推論時間參數超出限制')
        if self.mix_accompaniment and not self.separate_vocals:raise ValueError('混入伴奏需先分離人聲')

def prepare(presenter, demo_id, comparison, candidate, edited='', before=None, settings=None):
    audit=getattr(presenter,'excerpt',None)
    is_excerpt=bool(audit and audit.get('recording_id')==demo_id)
    settings=settings or (Settings(separate_vocals=False,mix_accompaniment=False) if is_excerpt else Settings());settings.validate()
    if is_excerpt and (settings.separate_vocals or settings.mix_accompaniment):raise ValueError('已核對 CSD 純人聲片段使用固定不分離／不混音設定')
    demo=presenter.demos.get(demo_id)
    if not demo or demo.language!='en' or not demo.original_segments:raise ValueError('請選擇原詞完整的英文Demo')
    if not comparison or comparison.get('demo_id')!=demo_id or comparison.get('source')!=demo.original_segments:raise ValueError('翻譯與Demo不相符，請載入對應比較')
    ids=[f'{demo_id}:{i+1:03d}' for i in range(len(demo.original_segments))]
    if comparison.get('segment_ids')!=ids:raise ValueError('翻譯片段ID不相符')
    if candidate=='edited':
        if not before or before.get('demo_id')!=demo_id:raise ValueError('請先為目前Demo載入候選並編輯')
        lines=edited.splitlines()
    elif candidate in ('direct','blt_assisted'):
        lines=comparison.get('modes',{}).get(candidate,{}).get('segments',[])
    else:raise ValueError('未知演唱候選')
    if len(lines)!=len(ids) or any(not isinstance(s,str) or not s.strip() or '|' in s or '\n' in s or '\r' in s for s in lines):raise ValueError('中文歌詞須每片段一行、不可空白或含|，片段數須與原詞一致')
    if any(not any('\u4e00' <= c <= '\u9fff' for c in s) for s in lines):raise ValueError('每個片段須包含中文字')
    root=presenter.root(demo)
    if not availability(demo,root)['complete']:raise ValueError('官方音訊不完整，不能推論')
    assets={k:str(safe_asset(root,getattr(demo,k))) for k in ('original_audio','melody_audio','timbre_audio')}
    # Ref text belongs exclusively to the timbre audio, not official target_text.
    submitted=[OpenCC('t2s').convert(s) for s in lines] if settings.simplify else list(lines)
    request={'demo_id':demo_id,'candidate':candidate,'segment_ids':ids,'original_reference_lyrics':demo.reference_text,
            'source_segments':list(demo.original_segments),'selected_traditional_segments':list(lines),
            'submitted_segments':submitted,'target_text':'|'.join(submitted),**assets,'settings':asdict(settings),
            'source_revision':demo.source_revision,'source_is_mock':comparison.get('is_mock',True),
            'input_audio_sha256':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in assets.items()}}
    if is_excerpt:
        if len(set(request['input_audio_sha256'].values()))!=1 or next(iter(request['input_audio_sha256'].values()))!=audit['audio_sha256']:raise ValueError('CSD片段音訊與核對紀錄不符')
        request['verified_excerpt']=audit
    return request

def configuration():
    python=os.getenv('HW2_SINGING_PYTHON',''); manifest=os.getenv('HW2_SINGING_MANIFEST','');issues=[];data={}
    if not python or not Path(python).is_file():issues.append('未設定可用HW2_SINGING_PYTHON獨立推論環境')
    if not manifest or not Path(manifest).is_file():issues.append('缺少本機權重manifest；不下載模型')
    else:
        try:
            data=json.loads(Path(manifest).read_text())
            if data.get('model_id')!=MODEL_ID or not data.get('revision'):issues.append('manifest模型ID或revision不符')
            for k in REQUIRED:
                if not Path(data.get(k,'')).is_absolute() or not Path(data.get(k,'')).is_file():issues.append('manifest缺少本機絕對路徑檔案：'+k)
            if any(not Path(data.get(k,'')).is_file() for k in ('separator_config','separator_checkpoint')):issues.append('人聲分離本機權重未準備')
        except (OSError,ValueError,TypeError,AttributeError):issues.append('權重manifest無法解析')
    if os.getenv('HW2_SINGING_ENABLED')!='1':issues.append('真實推論未啟用（HW2_SINGING_ENABLED=1）')
    return {'ready':not issues,'issues':issues,'python':python,'manifest':data}

def validate_output(path):
    samples,rate=sf.read(path,always_2d=True)
    if rate!=44100 or samples.shape[0]==0 or samples.shape[1] not in (1,2) or not np.isfinite(samples).all() or np.max(np.abs(samples))==0:raise ValueError('輸出音訊格式錯誤、非有限值或靜音')
    return {'sample_rate':rate,'frames':len(samples),'channels':samples.shape[1],'duration_seconds':len(samples)/rate,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}

class MockAdapter:
    def run(self,request,directory):
        return {'status':'mock_validated','is_mock':True,'audio':None,'message':'MOCK：僅驗證資料流程，未生成演唱或音訊。','settings':request['settings']}

class NativeAdapter:
    def __init__(self,root):self.root=Path(root)
    def run(self,request,directory):
        conf=configuration()
        if not conf['ready']:raise RuntimeError('；'.join(conf['issues']))
        if request['source_is_mock']:raise ValueError('真實演唱拒絕mock翻譯')
        if not request['settings']['separate_vocals']:
            audit=request.get('verified_excerpt',{})
            if audit.get('recording_id')!='CSD_en042a' or audit.get('audio_sha256')!=request['input_audio_sha256']['original_audio'] or request['settings']['mix_accompaniment']:raise ValueError('略過分離只允許已核對的CSD純人聲片段')
        payload={**request,'model':conf['manifest'],'root':str(self.root.resolve())}
        path=directory/'request.json';path.write_text(json.dumps(payload,ensure_ascii=False,indent=2));path.chmod(0o600)
        env={k:v for k,v in os.environ.items() if not k.startswith(('HW2_LLM_','GEMINI_','GOOGLE_API','HF_TOKEN','HUGGING_FACE_HUB_TOKEN'))}
        env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',WANDB_MODE='disabled',PYTHONDONTWRITEBYTECODE='1')
        # Private inference temporaries must never inherit the public NAS install TMPDIR.
        for name in ('tmp','cache','hf-offline'):(directory/name).mkdir(mode=0o700)
        env.update(TMPDIR=str((directory/'tmp').resolve()),XDG_CACHE_HOME=str((directory/'cache').resolve()),HF_HOME=str((directory/'hf-offline').resolve()),HF_HUB_CACHE=str((directory/'hf-offline/hub').resolve()))
        try:
            with (directory/'worker.log').open('w') as log:
                os.chmod(directory/'worker.log',0o600)
                p=subprocess.run([conf['python'],str(Path(__file__).with_name('worker.py')),str(path)],cwd=directory,env=env,stdout=log,stderr=log,timeout=600)
        except subprocess.TimeoutExpired:raise RuntimeError('YingMusic推論超過600秒，已停止；未重試') from None
        if p.returncode:raise RuntimeError('YingMusic worker失敗，詳見本機worker.log；未重試')
        audio=directory/'singing.wav';info=validate_output(audio)
        return {'status':'completed','is_mock':False,'audio':str(audio.resolve()),'audio_info':info,'model_id':MODEL_ID,'revision':conf['manifest']['revision'],'settings':request['settings'],'metrics':json.loads((directory/'metrics.json').read_text())}

class SingingController:
    def __init__(self,presenter,adapter=None,directory=OUTPUT):
        self.presenter=presenter;self.adapter=adapter or NativeAdapter(presenter.source_roots.get('yingmusic_official',Path('.')));self.directory=Path(directory)
    def generate(self,demo_id,comparison,candidate,edited='',before=None,settings=None):
        request=prepare(self.presenter,demo_id,comparison,candidate,edited,before,settings)
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        directory=self.directory/uuid.uuid4().hex;directory.mkdir(mode=0o700);start=time.monotonic()
        try:result=self.adapter.run(request,directory)
        except (ValueError,RuntimeError,OSError) as exc:result={'status':'failed','is_mock':isinstance(self.adapter,MockAdapter),'audio':None,'error':str(exc)}
        result.update(demo_id=demo_id,candidate=candidate,elapsed_seconds=round(time.monotonic()-start,3),request=request)
        record=directory/'result.json';record.write_text(json.dumps(result,ensure_ascii=False,indent=2));record.chmod(0o600)
        result['artifact_path']=str(record.resolve());return result

    def load_saved(self,demo_id,comparison,candidate,edited='',before=None,settings=None):
        request=prepare(self.presenter,demo_id,comparison,candidate,edited,before,settings)
        expected_revision=configuration()['manifest'].get('revision')
        files=sorted(self.directory.glob('*/result.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        for path in files:
            if path.is_symlink() or path.stat().st_size>2_000_000:continue
            try:
                result=json.loads(path.read_text())
                if (result.get('is_mock') is not False or result.get('status')!='completed'
                    or result.get('model_id')!=MODEL_ID or result.get('request')!=request
                    or expected_revision and result.get('revision')!=expected_revision):continue
                audio=Path(result['audio']).resolve()
                if not audio.is_relative_to(self.directory.resolve()) or audio!=path.parent.resolve()/'singing.wav':continue
                info=validate_output(audio)
                if info['sha256']!=result.get('audio_info',{}).get('sha256'):continue
                result['artifact_path']=str(path.resolve());return result
            except (OSError,ValueError,KeyError,RuntimeError):continue
        raise ValueError('此Demo／候選與目前文字尚無對應真實演唱；未重新推論')
