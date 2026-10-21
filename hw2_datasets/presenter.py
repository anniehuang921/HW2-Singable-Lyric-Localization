"""Bridge the CSD recording schema into the existing source-independent UI."""
from hw2_ui.presenter import Presenter
from hw2_ui.catalog import asset_info
from dataclasses import replace
from pathlib import Path

class DatasetPresenter(Presenter):
    def __init__(self,demos,source_roots,csd):
        self.csd=csd
        self.excerpt=None
        super().__init__([*demos,*[r.to_demo() for r in csd.recordings.values()]],{**source_roots,'csd':csd.root})

    def enable_excerpt(self,audit):
        self.excerpt=audit
        rid=audit['recording_id'];demo=self.demos[rid];filename=Path(audit['audio_path']).name
        self.source_roots['csd_excerpt']=Path(audit['audio_path']).parent
        self.demos[rid]=replace(demo,source_type='csd_excerpt',source_revision=demo.source_revision+':'+audit['audio_sha256'],
            original_segments=list(audit['segments']),reference_text='|'.join(audit['segments']),
            original_audio=filename,melody_audio=filename,timbre_audio=filename)

    def actionable(self,rid):
        return rid in self.demos and (self.demos[rid].source_type not in ('csd','csd_excerpt') or bool(self.excerpt and rid==self.excerpt['recording_id']))

    def choices(self,language='en',task='全部'):
        # Preserve existing official-demo dropdown and API filter semantics.
        result=super().choices(language,task)
        return [(label,value) for label,value in result if self.demos[value].source_type not in ('csd','csd_excerpt')]

    def select(self,demo_id):
        result=list(super().select(demo_id))
        if demo_id in self.csd.recordings:
            r=self.csd.recordings[demo_id]
            result[0]=f'### {r.title} · {r.key_variant}\nCSD · {r.language.upper()} · {r.duration:.2f} 秒 · CC BY-NC-SA 4.0\n\n歌曲 {r.song_id}；錄音 {r.recording_id}。\n\nPhase 4A 僅瀏覽與播放；後續需選取短片段及核對時間。'
            if r.language=='ko':result[0]+='\n\n韓文翻譯及來源演唱相容性待驗證。'
            if self.excerpt and demo_id==self.excerpt['recording_id']:
                result[0]=result[0].replace('Phase 4A 僅瀏覽與播放；後續需選取短片段及核對時間。','完整歌曲保留供瀏覽；翻譯與演唱限以下核對片段。')
                result[0]+='\n\n已核對 Phase 4B 片段：'+str(self.excerpt['start_seconds'])+'–'+str(self.excerpt['end_seconds'])+' 秒。下方翻譯與演唱只使用此兩句片段。'
                result[6]['verified_excerpt']=self.excerpt
                full=r.to_demo();result[2]=self.audio(full,'original_audio',asset_info(self.csd.root,r.audio_path))
            result[1]=r.lyrics # Preserve official whitespace/stanza boundaries verbatim.
            result[6].update(self.csd.details(demo_id))
            if self.excerpt and demo_id==self.excerpt['recording_id']:
                result[6]['translation_status']='已核對兩句片段；翻譯／演唱品質待人工聆聽'
                result[6]['line_timing_alignment']='已逐一核對14個官方音素與MIDI／CSV；邊界加餘量，未宣稱人工聽辨完成'
        return tuple(result)
