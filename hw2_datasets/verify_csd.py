"""Offline full CSD integrity/decoding/pairing audit, with private JSON output."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
import soundfile as sf
from .csd import CSD, DEFAULT_ROOT

PHONES={
'en':set('b d f g h j k l m n p r s t v w z zh ch sh th dh ng y ae ei e ii i ai a ou u ao uu oi au eo er oo'.split()),
'ko':set('g kk n d tt r l m b pp s ss ng j jj ch k t p h y w a ae eo e o u eu ui i oe'.split())}

def midi_notes(path):
    """Read standard MIDI note-on count without a new package dependency."""
    data=Path(path).read_bytes()
    if data[:4]!=b'MThd':raise ValueError('Invalid MIDI header')
    header_len=int.from_bytes(data[4:8],'big'); tracks=int.from_bytes(data[10:12],'big')
    pos=8+header_len; notes=0
    def vlq(buf,i):
        value=0
        for _ in range(4):
            b=buf[i];i+=1;value=value*128+(b&127)
            if b<128:return value,i
        raise ValueError('Invalid MIDI VLQ')
    for _ in range(tracks):
        if data[pos:pos+4]!=b'MTrk':raise ValueError('Missing MIDI track')
        size=int.from_bytes(data[pos+4:pos+8],'big'); buf=data[pos+8:pos+8+size];pos+=8+size;i=0;running=None
        while i<len(buf):
            _,i=vlq(buf,i);status=buf[i]
            if status>=128:i+=1
            elif running is not None:status=running
            else:raise ValueError('Invalid running status')
            if status==255:
                i+=1;n,i=vlq(buf,i);i+=n;running=None
            elif status in (240,247):n,i=vlq(buf,i);i+=n;running=None
            elif 128<=status<240:
                running=status;n=1 if status>>4 in (12,13) else 2
                if status>>4==9 and buf[i+1]>0:notes+=1
                i+=n
            else:raise ValueError('Unexpected MIDI event')
    return notes

def verify(root):
    dataset=CSD(root);rows=[]
    for r in dataset.recordings.values():
        labels=dataset.csv_rows(r.recording_id)
        phones=(dataset.root/r.annotations['txt']).read_text().split()
        notes=midi_notes(dataset.root/r.annotations['mid'])
        if not labels or len(labels)!=len(phones) or len(labels)!=notes:raise ValueError(r.recording_id+': MIDI/CSV/phoneme counts')
        if any(p not in PHONES[r.language] for syllable in phones for p in syllable.split('_')):raise ValueError(r.recording_id+': unknown phoneme')
        if [row['syllable'] for row in labels]!=phones:raise ValueError(r.recording_id+': CSV/phoneme sequence')
        previous=-1
        for row in labels:
            start,end=float(row['start']),float(row['end']);pitch=int(row['pitch'])
            if not 0<=start<end<=r.duration or start<previous or not 0<=pitch<=127:raise ValueError(r.recording_id+': timing/pitch')
            previous=start
        frames=0;peak=0.0
        with sf.SoundFile(dataset.root/r.audio_path) as audio:
            if audio.samplerate!=44100 or audio.subtype!='PCM_16':raise ValueError('Unexpected official WAV format')
            for block in audio.blocks(blocksize=65536,dtype='float32'):
                if not np.isfinite(block).all():raise ValueError('Nonfinite audio')
                peak=max(peak,float(np.max(np.abs(block))));frames+=len(block)
            if frames!=audio.frames or peak==0:raise ValueError('Invalid/silent audio')
        hashes={}
        for relative in [r.audio_path,*r.annotations.values()]:
            h=hashlib.sha256()
            with (dataset.root/relative).open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
            hashes[relative]=h.hexdigest()
        rows.append({'recording_id':r.recording_id,'song_id':r.song_id,'language':r.language,'duration':r.duration,
                     'notes':notes,'full_decode':True,'peak':peak,'sha256':hashes})
    counts={lang:{'songs':len({r.song_id for r in dataset.recordings.values() if r.language==lang}),
                  'recordings':sum(r.language==lang for r in dataset.recordings.values())} for lang in ['en','ko']}
    if counts!={'en':{'songs':50,'recordings':100},'ko':{'songs':50,'recordings':100}}:raise ValueError('Official counts mismatch')
    return {'counts':counts,'verified':len(rows),'recordings':rows,
            'limitations':['逐字聽辨與歌詞行時間對齊尚待人工核對；MIDI 驗證音符數而非重建 tempo 時間。']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=DEFAULT_ROOT);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    result=verify(args.root);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2));args.output.chmod(0o600)
    print(json.dumps({'counts':result['counts'],'verified':result['verified']}))
