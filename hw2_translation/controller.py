"""UI-facing workflow with explicit demo binding and real BLT edit validation."""
from .blt_bridge import Bridge
from .engine import Engine
from .providers import from_environment, ProviderError
from .storage import save, edit_record, DEFAULT_DIR
import json
import os
from pathlib import Path

class Controller:
    def __init__(self,presenter,provider_factory=from_environment,bridge=None,directory=None):
        self.presenter=presenter;self.provider_factory=provider_factory;self.bridge=bridge or Bridge();self.directory=directory
    def persist(self,record,kind):
        return save(record,kind,**({'directory':self.directory} if self.directory else {}))
    def translate(self,demo_id,progress=lambda text:None):
        demo=self.presenter.demos.get(demo_id)
        if not demo or demo.language!='en' or not demo.original_segments:
            raise ProviderError('請選擇原詞完整的英文 Demo（SingEdit_EN_01／02）')
        from hw2_ui.catalog import availability
        if not availability(demo,self.presenter.root(demo))['complete']:
            raise ProviderError('Demo 音訊或資料缺失；請先修復來源')
        provider=self.provider_factory()
        record=Engine(provider,self.bridge).run(demo,progress)
        record['artifact_path']=self.persist(record,'comparison')
        return record
    def load_saved(self,demo_id):
        demo=self.presenter.demos.get(demo_id)
        if not demo or not demo.original_segments:raise ValueError('原詞不完整，無法載入比較')
        directory=Path(self.directory) if self.directory else DEFAULT_DIR
        paths=sorted(directory.glob('comparison-*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        expected_model=os.getenv('HW2_LLM_MODEL','gemini-3.5-flash-lite')
        for path in paths:
            if path.is_symlink() or path.stat().st_size>2_000_000:continue
            try:record=json.loads(path.read_text())
            except (ValueError,OSError):continue
            if (record.get('demo_id')==demo_id and record.get('source')==demo.original_segments
                and record.get('is_mock') is False and record.get('provider',{}).get('model')==expected_model
                and all(record.get('modes',{}).get(mode,{}).get('segments') for mode in ('direct','blt_assisted'))):
                record['artifact_path']=str(path.resolve())
                return record
        raise ValueError('此 Demo 尚無對應模型的完整真實比較紀錄')

    def candidate(self,demo_id,record,mode):
        if not record or record['demo_id']!=demo_id:raise ValueError('沒有此 Demo 的翻譯，請先開始翻譯')
        lines=record.get('modes',{}).get(mode,{}).get('segments')
        if not lines:raise ValueError('所選版本尚未產生有效歌詞')
        return lines
    def edit(self,demo_id,record,mode,text,before_snapshot=None):
        before=self.candidate(demo_id,record,mode)
        if before_snapshot is not None:
            if before_snapshot['demo_id']!=demo_id or before_snapshot['mode']!=mode:raise ValueError('候選已變更，請重新載入候選')
            before=before_snapshot['lines']
        lines=text.splitlines()
        if len(lines)!=len(record['segment_ids']) or any(not s.strip() or '|' in s for s in lines):raise ValueError('每段一行、不可空行或含 |，段數須與原文一致')
        verification=self.bridge.validate(record['source'],lines)
        edit=edit_record(record,mode,before,lines,verification)
        edit['yingmusic_target_text']='|'.join(lines)
        edit['comparison_artifact']=record['artifact_path']
        return edit,self.persist(edit,'edit')
