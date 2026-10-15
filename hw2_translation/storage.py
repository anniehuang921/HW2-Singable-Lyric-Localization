"""Append-only comparison/edit JSON records; never store credentials."""
import json
import os
from pathlib import Path
import uuid

DEFAULT_DIR=Path(__file__).resolve().parents[1]/'artifacts'/'translations'

def save(record,kind='comparison',directory=DEFAULT_DIR):
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    name=f'{kind}-{uuid.uuid4().hex}.json';path=directory/name
    with path.open('x') as f:
        os.chmod(path,0o600);json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    return str(path)

def edit_record(comparison,candidate,before,after,validation):
    if len(after)!=len(comparison['segment_ids']):raise ValueError('中文段數必須與原文一致')
    return {'kind':'human_edit','demo_id':comparison['demo_id'],'segment_ids':comparison['segment_ids'],
            'source':comparison['source'],'candidate':candidate,'before':before,'after':after,
            'validation':validation,'is_mock':comparison['is_mock'],'provider':comparison['provider']}
