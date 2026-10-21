# HW2 Context

更新：2026-10-21（Asia/Taipei）。

BLT Fork為主Repo；原版src／skills／pyproject.toml／uv.lock不變，YingMusic獨立且唯讀。Phase1、2A／2B、3、4A及4B均已完成；Phase4B人工操作／播放驗收通過，語義／自然度／可唱性優劣尚未正式評分。

## 可重現介面

- BLT使用Python3.11原鎖檔；HW2_BLT_PYTHON可指定隔離環境Python。
- Gradio用獨立.venv-ui，GPU Worker用獨立Python3.10／torch2.7.1-cu128配套。環境版本與manifest範例見docs/phase3，權重不隨Repo提供。
- HW2_YINGMUSIC_ROOT指向合法取得唯讀官方Repo，預設sibling目錄。Catalog只AST讀preset，不import eager模型初始化。
- CSD完整資料本機ignored artifacts；HW2_CSD_ROOT可指定來源，50英文＋50韓文歌曲、200調性錄音，完整性／配對／解碼通過。
- 7864僅127.0.0.1，支援官方Demo與CSD瀏覽、同模型比較、編輯驗證與已生成音訊回播；僅已核對CSD_en042a兩句片段開放Phase4B工作流程，韓文只瀏覽。
- 透過Terminal隱藏輸入明確HW2_LLM_API_KEY，不讀其他程序憑證；原始詞／譯文／Prompt／response／音訊／本機manifest只保留artifacts，原始Session與完整備份只在Repo外私人位置。

## 真實結果與限制

Phase2B兩英文Demo同Gemini3.5Flash-Lite，Direct音節符合0/6、assisted6/6；Phase3 EN_01 assisted真實演唱完成。Phase4B成功本輪3請求／1283tokens，Direct音節[7,10]、assisted[7,7]且一次修訂押韻通過，兩者pattern不精確。兩版YingMusic約11.05秒，重載不需新API／GPU。先前兩次400認證失敗保留私人原始紀錄，用量未知。

完整公開統計見docs/phase4b/RESULTS.md；私人全文與精確WAV位置不隨Git散布。已知原版標點押韻與validator feedback限制保留；assisted是依Skill規則移植編排，不是完整原Agent流程。73項回歸及舊Demo／CSD／7863與7864回播通過。

## 本輪發布準備

人工只授權安全盤點、公開文件最小整理與提交計畫，不stage／commit／push、不切分支、不清理私人資料。既有完整工程文件在ignored私人快照保留；公開版省略主機磁碟拓樸、共享目錄與其他研究環境資訊。建議提交與分支時點見docs/RELEASE_PREPARATION.md。Phase4C較長片段／整曲與Phase4D操作改善只規劃，尚未實作。
