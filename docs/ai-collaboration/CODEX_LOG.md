# HW2 AI Collaboration — Public Summary

本文件為去識別化工程摘要。完整私人日誌、原始 Session、metadata、Prompt／譯文與備份驗證紀錄保留本機及 Repo 外私人備份，不包含於 Git。下列歷史摘要保留實際事件順序，不偽造開發時間。

## 2026-10-14 — Phase 1 與 Phase 2A

使用者批准隔離環境與 Baseline；AI 依原鎖檔同步核心依賴，未改核心。Baseline 21案16 pass、4 observation、1已知中文標點押韻失敗；原 validator feedback 與 pattern 限制保留。既有翻譯重評不是新模型生成。

使用者批准 Gradio UI；AI以 AST 讀取唯讀官方 presets，辨識8例、4英4中，兩個完整英文 Lyric Editing 可用。原詞來自同一原音訊的 reference annotation，不把不同音訊 ref_text 或 target_text 當原詞。音訊轉換快取在臨時目錄。官方音訊傳輸與缺失處理完成自動驗證，真人聽感待評。

## 2026-10-15 — Phase 2B

使用者批准同模型翻譯及2次有限修訂；AI新增 compatible provider、原版 BLT subprocess bridge、人工編輯保存。Mock 測試與真實結果分開。

使用者親自終端隱藏輸入 Key。2.5Flash 原生錯誤明確指出新使用者不可用；3.8Flash兩次503停止。人工批准3.5Flash-Lite，短測HTTP200生成OK.；本機精確比對問題修正而未再短測。模型參數0.2／4096／low／45秒，Direct與assisted相同。

兩Demo真實生成共6請求全200；tokens2557輸入＋713輸出。EN_01 assisted0修訂，EN_02實際2修訂；Direct精確音節0/6，assisted6/6，最終patterns都False。無同組重複押韻案例，語義／自然度／可唱性未人工評分。完整Prompt、原譯文與每次修訂保留私人檔，公開只含數值摘要。

44單元回歸通過，UI兩例保存比較／編輯驗證／音訊HTTP200及解碼通過。提供同UI saved-only檢閱模式避免重生成，未取舊程序Key，未進行YingMusic推論。

## 2026-10-15 — 首次公開審查

使用者條件式授權Commit／Push；AI發現素材再散布權與私人環境資訊，依條件停止，未stage／commit／push。44單元通過，Baseline既知結果重現；沒有API。

## 2026-10-16 — Public Release Cleanup

人工明確批准：完整備份後清理公開資料，重整僅未公開的本機初始化commit，階段性提交及非force push至指定Fork。遠端有新commit／分歧即停止。

實際遠端核對：fetch後origin/main仍是本機初始化的父commit；沒有遠端分支引用該本機初始化，符合重整條件。完整Git bundle與2458份工作檔備份逐檔SHA-256驗證成功，原始Session備份保留未覆寫。

AI修改：執行時Catalog Loader、可配置本機路徑、合成fixture測試、公開數值摘要、去識別化文件、私密檔案ignore保護。完整原文件保存於artifacts/private-release/，原始實驗不刪除。當前測試與提交結果另於完成驗證後補記。無新API、Billing、下載、核心／YingMusic修改。

### 2026-10-16T03:37:17+08:00 — 公開前驗證

- 47單元全部通過；無官方素材配置時47案例中37通過、10本機整合案例明確skip。兩次均不需要API Key。
- 原版Baseline21案重現16pass／4observation／1既知標點失敗，全部exit0；完整比較／編輯13份原檔與備份SHA-256一致。
- 暫時loopback UI成功讀兩Demo真實保存比較、編輯與原版重新驗證，provider明確禁止，沒有LLM呼叫。
- 分組採三筆：Baseline；UI＋Translation（app與controller相依，保持單筆可執行）；公開文件／協作摘要。依實際依賴合併Phase2A／2B，沒有偽造原開發時間。

- 公開前音訊smoke：EN_01／EN_02原詞載入、HTTP200、48000Hz，frames409434／395711，臨時UI關閉。
- 已建立Baseline commit 175207f；UI／Translation commit 33497c2c3ff84834b611587e2516de2f811674bf。各筆stage均明確列檔、diff --check與憑證／私人路徑／實際受限歌詞比對通過。新main不以舊私人初始化為祖先。
- 文件提交後再次fetch；只有原遠端未更新且fast-forward成立才Push。最終Push結果與本輪Session備份驗證保留私人release receipt及任務回報，避免commit自我引用。
