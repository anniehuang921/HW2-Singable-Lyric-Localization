"""Verify the official CSD archive and extract once without overwriting source data.
Run: python scripts/extract_csd.py artifacts/datasets/csd/CSD.zip
"""
import argparse
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path

ARCHIVE_SIZE=1850303574
EXPANDED_SIZE=3076407592
MD5='4c586caff29ca05264cf7223cad1b8a2'

def extract(archive):
    archive=Path(archive);destination=archive.parent
    if (destination/'CSD').exists():raise ValueError('CSD already exists; refusing to overwrite')
    if archive.stat().st_size!=ARCHIVE_SIZE:raise ValueError('Official archive size mismatch')
    md5=hashlib.md5();sha=hashlib.sha256()
    with archive.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):md5.update(block);sha.update(block)
    if md5.hexdigest()!=MD5:raise ValueError('Official MD5 mismatch')
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist())!=1015 or sum(x.file_size for x in z.infolist())!=EXPANDED_SIZE:raise ValueError('Official ZIP manifest mismatch')
        if shutil.disk_usage(destination).free<EXPANDED_SIZE+10*1024**3:raise ValueError('Local 10 GiB reserve gate')
        for item in z.infolist():
            path=Path(item.filename)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='CSD' or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Unsafe archive member')
        failed=z.testzip()
        if failed:raise ValueError('ZIP CRC failed: '+failed)
        z.extractall(destination)
    for p in (destination/'CSD').rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
    (destination/'CSD').chmod(0o700);archive.chmod(0o600)
    result={'source_url':'https://zenodo.org/records/4785016','archive_bytes':ARCHIVE_SIZE,'expanded_bytes':EXPANDED_SIZE,
            'entries':1015,'md5':md5.hexdigest(),'sha256':sha.hexdigest(),'zip_crc':'all entries passed'}
    receipt=destination/'import-receipt.json';receipt.write_text(json.dumps(result,indent=2));receipt.chmod(0o600)
    print(json.dumps(result))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);extract(ap.parse_args().archive)
