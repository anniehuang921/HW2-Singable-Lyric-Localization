"""Audited, immutable local CSD excerpt. No network/model calls."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
import soundfile as sf
from .csd import CSD
ROOT=Path(__file__).resolve().parents[1]/'artifacts/datasets/csd/excerpts'
MANIFEST=ROOT/'en042a-first-two.json'

def midi_events(path):
    data=Path(path).read_bytes();division=int.from_bytes(data[12:14],'big')
    if division&32768:raise ValueError('SMPTE MIDI unsupported')
    pos=8+int.from_bytes(data[4:8],'big');events=[]
    def vlq(buf,i):
        n=0
        while True:
            b=buf[i];i+=1;n=(n<<7)+(b&127)
            if b<128:return n,i
    for track in range(int.from_bytes(data[10:12],'big')):
        assert data[pos:pos+4]==b'MTrk';size=int.from_bytes(data[pos+4:pos+8],'big');buf=data[pos+8:pos+8+size];pos+=8+size
        i=0;tick=0;running=None
        while i<len(buf):
            delta,i=vlq(buf,i);tick+=delta;status=buf[i]
            if status>=128:i+=1
            else:status=running
            if status==255:
                typ=buf[i];i+=1;n,i=vlq(buf,i)
                if typ==81:events.append((tick,'tempo',int.from_bytes(buf[i:i+n],'big')))
                i+=n
            elif status in (240,247):n,i=vlq(buf,i);i+=n
            else:
                running=status;n=1 if status>>4 in (12,13) else 2
                if status>>4 in (8,9):events.append((tick,'on' if status>>4==9 and buf[i+1] else 'off',(status&15,buf[i],buf[i+1])))
                i+=n
    tempo=500000;last=0;seconds=0;active={};notes=[]
    for tick,kind,value in sorted(events,key=lambda x:x[0]):
        seconds+=(tick-last)*tempo/1e6/division;last=tick
        if kind=='tempo':tempo=value;continue
        key=value[:2]
        if kind=='on':active[key]=seconds
        elif key in active:notes.append({'start':active.pop(key),'end':seconds,'pitch':value[1]})
    return sorted(notes,key=lambda x:x['start'])

def build():
    c=CSD();r=c.recordings['CSD_en042a'];labels=c.csv_rows(r.recording_id);notes=midi_events(c.root/r.annotations['mid'])
    # Read official annotations at runtime; do not redistribute phoneme sequences.
    expected=(c.root/r.annotations['txt']).read_text(encoding='utf-8').split()[:14]
    assert len(expected)==14
    assert [x['syllable'] for x in labels[:14]]==expected
    for label,note in zip(labels[:15],notes[:15]):
        assert int(label['pitch'])==note['pitch']
        assert abs(float(label['start'])-note['start'])<0.001 and abs(float(label['end'])-note['end'])<0.001
    # Include real onset/offset breathing room; exclude next lyric beginning at14.1176.
    start,end=2.60,13.65;assert float(labels[14]['start'])>end
    samples,rate=sf.read(c.root/r.audio_path,dtype='float32');clip=samples[round(start*rate):round(end*rate)]
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    audio=ROOT/'en042a-first-two.wav'
    if MANIFEST.exists():return load()
    sf.write(audio,clip,rate,subtype='PCM_16');audio.chmod(0o600)
    def rms(a):return float(np.sqrt(np.mean(a*a)))
    audit={'recording_id':r.recording_id,'song_id':r.song_id,'source_url':'https://zenodo.org/records/4785016',
      'source_audio_sha256':hashlib.sha256((c.root/r.audio_path).read_bytes()).hexdigest(),
      'start_seconds':start,'end_seconds':end,'audio_path':str(audio.resolve()),'sample_rate':rate,'frames':len(clip),
      'audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'segments':r.to_demo().original_segments[:2],
      'csv_rows':[1,14],'phonemes':expected,'midi_csv_max_time_error_seconds':max(abs(float(x[k])-n[k]) for x,n in zip(labels[:14],notes[:14]) for k in ['start','end']),
      'first_note_start':float(labels[0]['start']),'last_note_end':float(labels[13]['end']),'next_note_start':float(labels[14]['start']),
      'lead_rms':rms(clip[:round((float(labels[0]['start'])-start)*rate)]),'tail_rms':rms(clip[round((float(labels[13]['end'])-start)*rate):]),
      'boundary_peak_first_10ms':float(np.max(abs(clip[:441]))),'boundary_peak_last_10ms':float(np.max(abs(clip[-441:]))),
      'alignment_evidence':'Official same-stem lyric first2lines; exact ordered14 phonemes; MIDI pitches/times match CSV within1ms; padded waveform decoded. Not a manual listening verdict.',
      'vocal_evidence':'Official CSD wav documented as vocal recording; no accompaniment track supplied. No separation/mixing.',
      'settings':{'separate_vocals':False,'mix_accompaniment':False}}
    MANIFEST.write_text(json.dumps(audit,ensure_ascii=False,indent=2));MANIFEST.chmod(0o600);return audit

def load():
    audit=json.loads(MANIFEST.read_text());audio=Path(audit['audio_path'])
    assert audit['recording_id']=='CSD_en042a' and audio.resolve().is_relative_to(ROOT.resolve())
    if hashlib.sha256(audio.read_bytes()).hexdigest()!=audit['audio_sha256']:raise ValueError('Excerpt audio hash mismatch')
    c=CSD();r=c.recordings[audit['recording_id']]
    if audit['segments']!=r.to_demo().original_segments[:2] or hashlib.sha256((c.root/r.audio_path).read_bytes()).hexdigest()!=audit['source_audio_sha256']:raise ValueError('Excerpt source changed')
    return audit

if __name__=='__main__':
    a=build();print(json.dumps({k:a[k] for k in ['recording_id','start_seconds','end_seconds','frames','midi_csv_max_time_error_seconds','boundary_peak_first_10ms','boundary_peak_last_10ms']},indent=2))
