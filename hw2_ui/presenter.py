"""Source-independent selection and on-demand browser-compatible audio."""
import hashlib
import os
from pathlib import Path
import tempfile
import soundfile as sf
from .catalog import availability, safe_asset

AUDIO_CACHE = Path(tempfile.gettempdir()) / f'hw2-ui-audio-{os.getuid()}'

class Presenter:
    def __init__(self, demos, source_roots):
        self.demos = {d.id: d for d in demos}
        self.source_roots = source_roots

    def root(self, demo):
        return self.source_roots[demo.source_type]

    def choices(self, language='en', task='全部'):
        demos = [d for d in self.demos.values() if (language == '全部' or d.language == language)
                 and (task == '全部' or d.task == task)]
        demos.sort(key=lambda d: (d.language != 'en', not availability(d, self.root(d))['complete'], d.id))
        return [(f'{d.name} · {d.language.upper()} · {d.task} · '
                 f'{"素材完整" if availability(d, self.root(d))["complete"] else "資料不完整"}', d.id) for d in demos]

    def audio(self, demo, key, info):
        if not info['available']:
            return None
        source = safe_asset(self.root(demo), getattr(demo, key))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        AUDIO_CACHE.mkdir(mode=0o700, exist_ok=True)
        target = AUDIO_CACHE / (digest + '.wav')
        if not target.exists():
            # Official WAVs include float32 and PCM24. Decode without ffmpeg,
            # cache PCM16 only for selected material; never write to the source.
            samples, rate = sf.read(source, dtype='float32', always_2d=True)
            with tempfile.NamedTemporaryFile(dir=AUDIO_CACHE, suffix='.wav', delete=False) as f:
                temporary = Path(f.name)
            try:
                sf.write(temporary, samples, rate, subtype='PCM_16')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        return str(target)

    def select(self, demo_id):
        demo = self.demos.get(demo_id)
        if demo is None:
            return '沒有可選的 Demo，或 Demo ID 不存在。', '', None, None, None, '', {}
        root = self.root(demo)
        status = availability(demo, root)
        metadata = {'demo_id': demo.id, 'name': demo.name, 'language': demo.language, 'task': demo.task,
                    'source_type': demo.source_type, 'source_url': demo.source_url,
                    'source_revision': demo.source_revision, 'evidence': demo.evidence,
                    'original_text_evidence': demo.original_text_evidence,
                    'original_segments': demo.original_segments, **status}
        summary = f'### {demo.name}\n{demo.language.upper()} · {demo.task} · '
        summary += '素材完整（官方設定對應；聽感待確認）' if status['complete'] else '資料不完整'
        if status['missing']:
            summary += '\n\n' + '\n'.join('- ' + reason for reason in status['missing'])
        if demo.original_audio == demo.melody_audio:
            summary += '\n\n原始演唱與旋律使用同一音訊。'
        paths = {}
        for key, info in status['assets'].items():
            try:
                paths[key] = self.audio(demo, key, info)
            except (RuntimeError, OSError, ValueError) as exc:
                paths[key] = None
                summary += f'\n\n{key} 無法載入：{exc}'
        melody = None if demo.melody_audio == demo.timbre_audio else paths['melody_audio']
        return summary, demo.original_lyrics, paths['original_audio'], melody, paths['timbre_audio'], demo.reference_text.replace('|', '\n'), metadata
