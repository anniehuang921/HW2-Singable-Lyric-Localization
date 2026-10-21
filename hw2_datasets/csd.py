"""Read-only official CSD adapter: songs and key recordings have distinct IDs."""
from __future__ import annotations
import csv
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
import soundfile as sf
from hw2_ui.catalog import Demo, safe_asset

SOURCE = 'https://zenodo.org/records/4785016'
LICENSE = 'CC BY-NC-SA 4.0'
DEFAULT_ROOT = Path(os.environ.get('HW2_CSD_ROOT', Path(__file__).resolve().parents[1]/'artifacts/datasets/csd/CSD'))

@dataclass(frozen=True)
class Recording:
    song_id: str
    recording_id: str
    language: str
    key_variant: str
    title: str
    duration: float
    audio_path: str
    lyrics: str
    annotations: dict
    metadata: dict

    def to_demo(self):
        """Provide the existing workflow schema without inventing line timings.

        Raw lyrics retain stanza boundaries separately. Nonempty official lines
        are ordered source segments, NOT automatically aligned singing excerpts.
        """
        return Demo(self.recording_id, self.title+' · '+self.key_variant, self.language,
                    'CSD Singing', 'csd', SOURCE, '4785016', 'CSD official metadata and same-stem files',
                    [line.strip() for line in self.lyrics.splitlines() if line.strip()],
                    '同 stem 官方 lyric；CSV 以音節標註，尚未建立歌詞行與時間的人工核對對齊。',
                    self.audio_path, self.audio_path, self.audio_path,
                    '|'.join(line.strip() for line in self.lyrics.splitlines() if line.strip()), '',
                    [LICENSE, '完整歌曲僅供瀏覽；Phase 4B 需先選短片段並核對行／時間對齊。',
                     '韓文翻譯與來源演唱相容性待驗證。' if self.language=='ko' else '本階段不翻譯、不合成。'])

class CSD:
    def __init__(self, root=DEFAULT_ROOT):
        self.root=Path(root).resolve()
        if not self.root.is_dir():raise ValueError('CSD 尚未安裝；請設定 HW2_CSD_ROOT 至官方解壓目錄')
        self.recordings={}
        for folder,language in [('english','en'),('korean','ko')]:
            metadata=json.loads(safe_asset(self.root,f'{folder}/metadata.json').read_text(encoding='utf-8'))
            for stem,info in sorted(metadata.items()):
                if not re.fullmatch(('kr' if language=='ko' else 'en')+r'\d{3}[ab]',stem):raise ValueError('非預期 CSD recording stem')
                paths={k:f'{folder}/{k}/{stem}{ext}' for k,ext in [('wav','.wav'),('lyric','.txt'),('mid','.mid'),('csv','.csv'),('txt','.txt')]}
                for path in paths.values():
                    if not safe_asset(self.root,path).is_file():raise ValueError(f'CSD 配對檔案缺失：{path}')
                lyrics=safe_asset(self.root,paths['lyric']).read_text(encoding='utf-8')
                if not lyrics.strip():raise ValueError('CSD 歌詞為空')
                audio=sf.info(safe_asset(self.root,paths['wav']))
                if audio.frames<=0:raise ValueError('CSD 音訊為空')
                rid='CSD_'+stem
                self.recordings[rid]=Recording('CSD_'+stem[:-1],rid,language,stem[-1],info['songname'],
                    audio.duration,paths['wav'],lyrics,{k:v for k,v in paths.items() if k!='wav'},dict(info))
        # Refuse silent extra/missing recordings in the actual source tree.
        for folder,lang in [('english','en'),('korean','ko')]:
            found={p.stem for p in (self.root/folder/'wav').glob('*.wav')}
            expected={r.recording_id[4:] for r in self.recordings.values() if r.language==lang}
            if found!=expected:raise ValueError('CSD WAV 與 metadata 清單不一致')
        grouped={}
        for r in self.recordings.values():grouped.setdefault(r.song_id,[]).append(r)
        for rows in grouped.values():
            if {r.key_variant for r in rows}!={'a','b'} or len({(r.title.casefold(),r.language) for r in rows})!=1:
                raise ValueError('CSD 每首歌曲必須有相同名稱的 a／b 兩份錄音')

    def songs(self,language='en'):
        titles={}
        for r in self.recordings.values():
            if language=='全部' or r.language==language:titles.setdefault(r.song_id,r.title)
        return sorted((title,song_id) for song_id,title in titles.items())

    def variants(self,song_id):
        return [(f'{r.key_variant} · 移調 {r.metadata["key_diff"]:+d} 半音',r.recording_id)
                for r in self.recordings.values() if r.song_id==song_id]

    def details(self,recording_id):
        r=self.recordings[recording_id]
        return {**asdict(r),'source_url':SOURCE,'license':LICENSE,
                'license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'translation_status':'待選取與核對片段；未執行' if r.language=='en' else '韓文翻譯及來源演唱相容性待驗證',
                'line_timing_alignment':'未建立；CSV 為音節時間，不能直接當作歌詞行時間'}

    def csv_rows(self,recording_id):
        r=self.recordings[recording_id]
        with safe_asset(self.root,r.annotations['csv']).open(encoding='utf-8',newline='') as stream:
            return list(csv.DictReader(stream))
