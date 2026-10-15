# HW2 Context

更新：2026-10-16（Asia/Taipei）。

本專案沿用 BLT Fork；原版 src/、skills/、pyproject.toml、uv.lock 保持不變。Phase 1 本機 Baseline、Phase 2A 官方 Demo UI、Phase 2B 同模型 Direct／BLT-assisted 比較均已完成。YingMusic 只讀，尚未整合模型演唱或 YouTube。

## 環境與操作

- BLT：獨立 hw2-blt Conda 環境，Python 3.11；以原 uv.lock 安裝核心依賴。
- UI：獨立 .venv-ui；依賴見 docs/phase2b/ui-requirements.txt。
- HW2_BLT_PYTHON 指向 BLT Python。預設為使用者家目錄下 .conda/envs/hw2-blt/bin/python。
- HW2_YINGMUSIC_ROOT 指向本機唯讀官方 Repo；預設為本專案的 sibling YingMusic-Singer-Plus。
- 官方 Catalog 執行時以 AST 讀取官方 app_local.py 的 literal presets，不 import 模型程式，不在 Git 保存歌詞。
- 完整譯文、修訂、Prompt 保留 artifacts/translations/；早期證據仍在被忽略的本機 docs 子目錄。私人整理前快照及完整 Git bundle 位於 Repo 外，位置記私人 release manifest。
- 公開工程摘要見 CODEX_LOG.md；原始 Session／metadata 與備份登記只存 Repo 外私人位置。

## 實測與限制

Baseline 21 案例：16 pass、4 observations、1 既知句尾標點押韻 expectation failure。Phase 2A 官方8例（4英／4中），4個 Lyric Editing 完整，其中2英文；4個 Melody Control 缺可查證旋律原詞。

2026-10-15 Gemini 真實比較：gemini-3.5-flash-lite，兩英文 Demo 共6次生成，3270 tokens。Direct音節精確0/6、assisted6/6；修訂0與2次。最終字詞音節 pattern 均不精確符合。尚未人工驗收自然度、語義與可唱性。公開數值見 docs/phase2b/public-summary.json。

2026-10-16 使用者授權清理、重整僅未公開初始化 commit 並非 force push 至自己的 Fork。先 fetch 核對祖先、完整備份，再清理。無新 API、模型、Billing 或演唱整合。
