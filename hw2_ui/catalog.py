"""Normalized material catalog and a read-only YingMusic adapter."""
from __future__ import annotations
import ast
import os
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import soundfile as sf

DEFAULT_ROOT = Path(os.environ.get('HW2_YINGMUSIC_ROOT', Path(__file__).resolve().parents[2] / 'YingMusic-Singer-Plus'))
CATALOG_FILE = Path(__file__).with_name('demo_catalog.json')

@dataclass(frozen=True)
class Demo:
    id: str
    name: str
    language: str
    task: str
    source_type: str
    source_url: str
    source_revision: str
    evidence: str
    original_segments: list[str] | None
    original_text_evidence: str | None
    original_audio: str | None
    melody_audio: str | None
    timbre_audio: str | None
    reference_text: str
    official_target_text: str
    notes: list[str]

    @property
    def original_lyrics(self):
        return '\n'.join(self.original_segments) if self.original_segments is not None else ''


def safe_asset(root: Path, relative: str | None) -> Path | None:
    if relative is None:
        return None
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('素材路徑超出來源目錄')
    return path


def asset_info(root: Path, relative: str | None) -> dict:
    if not relative:
        return {'available': False, 'reason': '官方設定未提供對應素材', 'path': None}
    try:
        path = safe_asset(root, relative)
        if not path.is_file():
            return {'available': False, 'reason': '素材路徑不存在', 'path': relative}
        info = sf.info(path)
        if info.frames <= 0:
            raise ValueError('音訊沒有取樣資料')
        return {'available': True, 'path': relative, 'duration_seconds': round(info.duration, 3),
                'sample_rate': info.samplerate, 'channels': info.channels, 'subtype': info.subtype}
    except (ValueError, RuntimeError, OSError) as exc:
        return {'available': False, 'reason': f'音訊無法讀取：{exc}', 'path': relative}


def availability(demo: Demo, root: Path) -> dict:
    assets = {key: asset_info(root, getattr(demo, key))
              for key in ('original_audio', 'melody_audio', 'timbre_audio')}
    missing = []
    if not demo.original_segments:
        missing.append('缺少 melody 音訊的原始歌詞；ref_text 僅屬 timbre，不採用 target_text 代替')
    for key, info in assets.items():
        if not info['available']:
            missing.append(f'{key}：{info["reason"]}')
    return {'complete': not missing, 'missing': missing, 'assets': assets,
            'line_count': len(demo.original_segments) if demo.original_segments else None}


def read_catalog(path: Path | None = None, *, root: Path = DEFAULT_ROOT) -> list[Demo]:
    # Default is always the local official source; never ship or prefer a stale private snapshot.
    data = json.loads(path.read_text()) if path is not None else build_catalog(root)
    if data['schema_version'] != 1:
        raise ValueError('不支援的 Catalog 版本')
    demos = [Demo(**row) for row in data['demos']]
    if len({d.id for d in demos}) != len(demos):
        raise ValueError('重複 Demo ID')
    return demos


def build_catalog(root: Path = DEFAULT_ROOT) -> dict:
    """Parse literal presets only. Never import the model app or run its code."""
    source = root / 'app_local.py'
    tree = ast.parse(source.read_text())
    presets = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('EXAMPLES_LYRIC_EDIT', 'EXAMPLES_MELODY_CONTROL'):
                    presets[target.id] = (ast.literal_eval(node.value), node.lineno)
    if set(presets) != {'EXAMPLES_LYRIC_EDIT', 'EXAMPLES_MELODY_CONTROL'}:
        raise ValueError('官方 preset 結構已變更，請人工核對 adapter')
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    demos = []
    for key, (rows, lineno) in presets.items():
        for row in rows:
            if len(row) != 11 or not all(isinstance(x, str) for x in row[:4]):
                raise ValueError('官方 preset 欄位已變更')
            timbre, melody, ref_text, target = row[:4]
            name = Path(melody).stem.removesuffix('_melody')
            language = 'en' if '_EN_' in name else 'zh' if '_ZH_' in name else 'unknown'
            same = safe_asset(root, timbre) == safe_asset(root, melody)
            # Same waveform plus the official reference annotation establishes the association.
            segments = ref_text.split('|') if same else None
            demos.append(asdict(Demo(name, name, language,
                'Lyric Editing' if key == 'EXAMPLES_LYRIC_EDIT' else 'Melody Control',
                'yingmusic_official', 'https://github.com/ASLP-lab/YingMusic-Singer-Plus', revision,
                f'app_local.py:{lineno} {key}', segments,
                '官方 preset 的 ref_audio 與 melody_audio 相同；ref_text 為該音訊歌詞。聽感對齊待人工確認。' if same else None,
                melody, melody, timbre, ref_text, target,
                [] if same else ['timbre 與 melody 不同，無可查證的 melody 原詞；official_target_text 是生成目標，不是原詞。'])))
    demos.sort(key=lambda d: (d['language'] != 'en', d['original_segments'] is None, d['id']))
    return {'schema_version': 1, 'source_file_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'demos': demos, 'inspection': {d['id']: availability(Demo(**d), root) for d in demos}}

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--yingmusic-root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--output', type=Path, default=Path('artifacts/catalog/demo_catalog.json'))
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.output.write_text(json.dumps(build_catalog(args.yingmusic_root), ensure_ascii=False, indent=2) + '\n')
    args.output.chmod(0o600)
