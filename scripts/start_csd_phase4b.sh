#!/usr/bin/env bash
# Exactly one song, max4 translation requests; no preflight or automatic retry.
set +x
set -euo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
.venv-ui/bin/python - <<'PY'
from hw2_datasets.excerpt import load
assert load()['recording_id']=='CSD_en042a'
PY
export HW2_SINGING_PYTHON="$HOME/.conda/envs/hw2-yingmusic/bin/python"
export HW2_SINGING_MANIFEST="$PWD/artifacts/deployment/singing-manifest.json" HW2_SINGING_ENABLED=1
.venv-ui/bin/python - <<'PY'
import shutil
from hw2_singing.adapter import configuration
assert shutil.disk_usage('.').free>=10*1024**3,'本機未保留10GiB'
c=configuration()
if not c['ready']:raise SystemExit('；'.join(c['issues']))
PY
unset HW2_LLM_API_KEY
IFS= read -r -s -p '請輸入 Tech HW2 Gemini API Key（隱藏輸入）：' HW2_LLM_API_KEY </dev/tty
printf '\n' >/dev/tty
[[ -n "$HW2_LLM_API_KEY" ]] || exit 1
export HW2_LLM_API_KEY HW2_LLM_AUTHORIZED=1 HW2_LLM_PROVIDER=google-gemini-openai-compatible
.venv-ui/bin/python -m hw2_translation.credential_check
export HW2_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
export HW2_LLM_MODEL=gemini-3.5-flash-lite HW2_LLM_BILLING=free-tier
export HW2_LLM_MAX_TOKENS=4096 HW2_LLM_REASONING_EFFORT=low HW2_LLM_TIMEOUT=45 HW2_LLM_REQUEST_LIMIT=4
export HW2_SINGING_PYTHON="$HOME/.conda/envs/hw2-yingmusic/bin/python"
export HW2_SINGING_MANIFEST="$PWD/artifacts/deployment/singing-manifest.json" HW2_SINGING_ENABLED=1
export HW2_CSD_PHASE4B=1 PYTHONDONTWRITEBYTECODE=1 GRADIO_ANALYTICS_ENABLED=False PYTHONPATH="$PWD"
.venv-ui/bin/python scripts/run_csd_first_singing.py
# Only after successful experiment, replace this project's 7864; never inspect environ.
.venv-ui/bin/python - <<'PY'
import os,signal,subprocess,time
from pathlib import Path
p=subprocess.run(['fuser','-n','tcp','7864'],capture_output=True,text=True)
for token in p.stdout.split():
 if not token.isdigit():continue
 proc=Path('/proc')/token;args=[x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
 assert proc.stat().st_uid==os.getuid() and (proc/'cwd').resolve()==Path.cwd()
 assert 'hw2_ui.app' in args and args[args.index('--port')+1]=='7864'
 os.kill(int(token),signal.SIGTERM)
PY
exec .venv-ui/bin/python -m hw2_ui.app --port 7864 --singing
