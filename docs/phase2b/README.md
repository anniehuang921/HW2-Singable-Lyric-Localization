# Phase 2B — Translation and Evaluation

同一Gradio提供Direct／BLT-assisted、原版音節／押韻／pattern驗證、最多2修訂、候選人工編輯與before／after保存。沿用BLT Skill規則的移植編排，並非完整Claude Agent重現。Direct不加入音樂限制；兩模式同模型／設定。真實數值見[public-summary.json](public-summary.json)，完整歌詞／Prompt／修訂留本機。

## 環境與啟動

Python3.11，獨立`.venv-ui`依`ui-requirements.txt`安裝；BLT環境依原鎖檔核心依賴。設定`HW2_BLT_PYTHON`與`HW2_YINGMUSIC_ROOT`，見Phase2A說明。測試不需要Gemini Key。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-ui/bin/python -m unittest discover -s tests -v
.venv-ui/bin/python -m hw2_ui.app --port 7863 --saved-only
```

檢閱模式：選英文Demo→載入已保存真實比較→選候選→編輯→重新驗證保存。需要本機`artifacts/translations/comparison-*.json`，乾淨clone沒有真實譯文，會明確顯示尚無紀錄。只有本機素材的live測試需對應官方來源及保存結果。公開fixture是合成資料，不是真實生成。

## Gemini 安全操作（會消耗配額，測試套件不執行）

既有真實短測成功者，先設定`HW2_PREFLIGHT_EVIDENCE`指向私人成功紀錄，執行`bash scripts/start_gemini_translation_ui.sh`。既有部署預設保留`artifacts/gemini/preflight.json`。此腳本僅離線核對證據，不重發短測，終端隱藏輸入Key後exec UI於127.0.0.1:7863。Key不進argv／檔案／Git，程序最多8生成請求，錯誤即停止且不自動重試。

首次配置可選`bash scripts/start_gemini_ui.sh`：一次真實短測通過再啟UI，原gate保留。不要在沒有授權時執行。固定gemini-3.5-flash-lite／Google compatible endpoint、temperature0.2、max_tokens4096、reasoning_effort low、timeout45；Free Tier由使用者專案管理，程式不啟用Billing。

手動adapter配置使用`HW2_LLM_PROVIDER`、`HW2_LLM_BASE_URL`、`HW2_LLM_MODEL`、`HW2_LLM_API_KEY`、`HW2_LLM_AUTHORIZED=1`。Codex Session不是UI API，不讀其他程序Key。原生／compatible獨立最小diagnostic模組保留，回應安全遮蔽；本輪未呼叫。

## 實測比較與限制

2026-10-15非mock：兩英文Demo共6生成calls，3270tokens。EN_01目標[8,6]，Direct[11,9]、assisted[8,6]，0修訂。EN_02目標[6,3,4,2]，Direct[7,5,7,6]；assisted[8,3,5,2]→[6,3,4,2]→相同，最後去除字間空格，2修訂。原韻式AB／ABCD最終符合，但無重複同組韻式，不能證明一般押韻能力。最終pattern全部不精確符合。原版validator feedback／標點問題保留。自然度、語義／情緒意象與可唱性均待人工，不將音節符合當品質結論。沒有YingMusic演唱、YouTube或新模型部署。
