"""Offline isolated worker calling the official model class, never app_local/infer_api.
Only launched after explicitly configured local checkpoint files and environment.
"""
import json
import argparse
import time
import os
from pathlib import Path
import socket
import sys


def main():
    ap=argparse.ArgumentParser();ap.add_argument('request');ap.add_argument('--load-only',action='store_true');args=ap.parse_args()
    request=json.loads(Path(args.request).read_text());job=Path.cwd();root=Path(request['root']);model_info=request['model'];started=time.monotonic();metrics={}
    # Official tokenizer uses ./src/...; link read-only source into the HW2 job directory.
    if not (job/'src').exists():(job/'src').symlink_to(root/'src',target_is_directory=True)
    sys.path.insert(0,str(root));os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    def offline(*args,**kwargs):raise RuntimeError('Network disabled in HW2 singing worker')
    socket.socket.connect=offline;socket.socket.connect_ex=offline;socket.create_connection=offline
    import torch
    import torchaudio
    if not torch.cuda.is_available():raise RuntimeError('CUDA不可用，未進行CPU推論')
    from src.YingMusicSinger.infer.YingMusicSinger import YingMusicSinger
    from src.third_party.MusicSourceSeparationTraining.inference_api import Separator
    torch.cuda.reset_peak_memory_stats()
    def load_model():
        start=time.monotonic()
        model=YingMusicSinger(**{k:model_info[k] for k in ('model_cfg_path','ckpt_path','vae_config_path','vae_ckpt_path','midi_teacher_ckpt_path')}).to('cuda').eval()
        torch.cuda.synchronize();metrics['model_load_seconds']=time.monotonic()-start
        return model
    def save_metrics(stage):
        metrics.update(stage=stage,total_seconds=time.monotonic()-started,gpu_name=torch.cuda.get_device_name(),peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
        path=job/'metrics.json';path.write_text(json.dumps(metrics,indent=2));path.chmod(0o600)
    if args.load_only:
        start=time.monotonic()
        separator=Separator(config_path=model_info['separator_config'],checkpoint_path=model_info['separator_checkpoint'],device='cuda')
        torch.cuda.synchronize();metrics['separator_load_seconds']=time.monotonic()-start
        del separator;torch.cuda.empty_cache()
        model=load_model();save_metrics('model_loaded');print('MODEL_AND_SEPARATOR_LOAD_SUCCESS',flush=True);return
    # Explicit local paths avoid both official inconsistent hub IDs and download_files().
    settings=request['settings'];ref=request['timbre_audio'];melody=request['melody_audio'];accompaniment=None
    separation_start=time.monotonic()
    if settings['separate_vocals']:
        separator=Separator(config_path=model_info['separator_config'],checkpoint_path=model_info['separator_checkpoint'],device='cuda')
        cache={}
        for source in dict.fromkeys([ref,melody]):
            wav,rate=torchaudio.load(source);vocals,inst,out_rate=separator.separate(wav,rate)
            v=job/f'vocals-{len(cache)}.wav';a=job/f'accompaniment-{len(cache)}.wav'
            torchaudio.save(str(v),torch.from_numpy(vocals),out_rate);torchaudio.save(str(a),torch.from_numpy(inst),out_rate);cache[source]=(str(v),str(a))
        ref=cache[ref][0];melody,accompaniment=cache[melody]
        del separator
        torch.cuda.empty_cache()
    metrics['separation_seconds']=time.monotonic()-separation_start
    model=load_model()
    params={k:settings[k] for k in ('seed','nfe_step','cfg_strength','t_shift','sil_len_to_end')}
    inference_start=time.monotonic()
    with torch.inference_mode():
        audio,rate=model(ref_audio_path=ref,melody_audio_path=melody,ref_text=request['original_reference_lyrics'],target_text=request['target_text'],lrc_align_mode='sentence_level',**params)
    torch.cuda.synchronize();metrics['synthesis_seconds']=time.monotonic()-inference_start
    audio=audio.cpu()
    if settings['mix_accompaniment'] and accompaniment:
        inst,inst_rate=torchaudio.load(accompaniment)
        if inst_rate!=rate:inst=torchaudio.functional.resample(inst,inst_rate,rate)
        if audio.shape[0]!=inst.shape[0]:
            if audio.shape[0]==1:audio=audio.expand(inst.shape[0],-1)
            elif inst.shape[0]==1:inst=inst.expand(audio.shape[0],-1)
            else:raise ValueError('不支援的聲道對應')
        length=min(audio.shape[1],inst.shape[1]);audio=audio[:,:length]+inst[:,:length]
        audio=audio/max(1.0,float(audio.abs().max()))
    torchaudio.save(str(job/'singing.wav'),audio,rate)
    for p in job.glob('*.wav'):p.chmod(0o600)
    save_metrics('completed')
    print('SYNTHESIS_SUCCESS',flush=True)

if __name__=='__main__':main()
