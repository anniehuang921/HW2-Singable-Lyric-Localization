#!/usr/bin/env bash
# Phase 3 review/singing only: no LLM credential or translation requests.
set +x
set -euo pipefail
umask 077
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$repo_root"
export HW2_SINGING_PYTHON="${HW2_SINGING_PYTHON:-$HOME/.conda/envs/hw2-yingmusic/bin/python}"
export HW2_SINGING_MANIFEST="${HW2_SINGING_MANIFEST:-$repo_root/artifacts/deployment/singing-manifest.json}"
export HW2_SINGING_ENABLED=1
export GRADIO_ANALYTICS_ENABLED=False
export PYTHONDONTWRITEBYTECODE=1
unset HW2_LLM_API_KEY GEMINI_API_KEY GOOGLE_API_KEY HF_TOKEN
.venv-ui/bin/python - <<'PY'
from hw2_singing.adapter import configuration
c=configuration()
if not c['ready']:raise SystemExit('未啟動：'+'；'.join(c['issues']))
PY
exec .venv-ui/bin/python -m hw2_ui.app --port 7864 --saved-only --singing
