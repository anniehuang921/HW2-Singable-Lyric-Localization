#!/usr/bin/env bash
# No API preflight: use the saved successful test. Run in the user's terminal. Never put the secret in argv, a file, or shell history.
set +x
set -euo pipefail
umask 077
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$repo_root"
if (( $# != 0 )); then
  echo "本啟動方式固定使用7863，不接受額外參數。" >&2
  exit 1
fi
ui_port=7863
if [[ ! "$ui_port" =~ ^[0-9]+$ ]] || (( ui_port < 1024 || ui_port > 65535 )); then
  echo '請使用 1024–65535 的本機端口。' >&2
  exit 1
fi
if [[ ! -x .venv-ui/bin/python ]]; then
  echo '找不到既有 .venv-ui/bin/python，未安裝或呼叫 API。' >&2
  exit 1
fi
# Check before collecting a credential; never kill a process occupying the port.
.venv-ui/bin/python - "$ui_port" <<'PY'
import socket, sys
with socket.socket() as s:
    try:s.bind(('127.0.0.1', int(sys.argv[1])))
    except OSError:
        print('該本機端口已使用；請改用另一端口，或在原 UI 終端按 Ctrl+C。', file=sys.stderr)
        raise SystemExit(1)
PY
.venv-ui/bin/python -m hw2_translation.verify_preflight
unset HW2_LLM_API_KEY
IFS= read -r -s -p '請輸入 Tech HW2 的 Gemini API Key（輸入不顯示）：' HW2_LLM_API_KEY </dev/tty
printf '\n' >/dev/tty
if [[ -z "$HW2_LLM_API_KEY" ]]; then
  echo 'API Key 為空，未啟動服務。' >&2
  exit 1
fi
export HW2_LLM_API_KEY
export HW2_LLM_AUTHORIZED=1
export HW2_LLM_PROVIDER='google-gemini-openai-compatible'
export HW2_LLM_BASE_URL='https://generativelanguage.googleapis.com/v1beta/openai/'
export HW2_LLM_MODEL='gemini-3.5-flash-lite'
export HW2_LLM_BILLING='free-tier'
export HW2_LLM_MAX_TOKENS=4096
export HW2_LLM_REASONING_EFFORT=low
export HW2_LLM_TIMEOUT=45
export HW2_LLM_REQUEST_LIMIT=8
export GRADIO_ANALYTICS_ENABLED=False
export PYTHONDONTWRITEBYTECODE=1
printf '啟動本機 UI：127.0.0.1:%s；請保留此終端，不要先按翻譯。\n' "$ui_port"
exec .venv-ui/bin/python -m hw2_ui.app --port "$ui_port"
