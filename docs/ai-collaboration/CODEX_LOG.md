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

### 2026-10-16 — 最終驗證與 GitHub 認證阻礙

- 從已提交HEAD用git archive建立無私人檔案的乾淨公開目錄，47測試中37通過、10官方素材整合skip（34.524秒），沒有Key或原始實驗依賴。
- 三筆既有提交：175207ff83b748c68b252f9124556656150381db Baseline；33497c2c3ff84834b611587e2516de2f811674bf UI與Translation；9de7edb0aa81118fea394c2769c97b6b6bee07a0 公開工程文件。
- 實際嘗試git push origin main；HTTPS因無可用認證／無互動終端而停止；唯讀SSH檢查亦認證失敗。沒有變更遠端、沒有force、沒有讀取或顯示憑證。GitHub main仍為原上游基準。
- 本筆文件提交補記已完成的測試與阻礙；全部本機成果／私人原檔保留，等待使用者在Remote SSH Terminal配置或互動提供GitHub認證後才能完成Push。不是授權不足，也不是遠端歷史衝突。

## 2026-10-16至2026-10-21 — Phase3至4B公開工程摘要

- 人工決策：主Repo開發、BLT／YingMusic上游唯讀；隔離GPU環境及必要模型在核准後部署，固定同源／模型／推論參數公平比較。私人詞／譯文／Prompt／response／音訊／Session不公開。完整歷次日誌及本輪整理前版本已逐檔私人快照保留。
- Phase3：Python3.10.22／torch2.7.1-cu128配套及RTX5090實際CUDA運算、固定Plus權重SHA／schema核對與載入通過。Worker離線、本機暫存；EN_01 assisted真實演唱成功，55回歸通過。曾遇動態依賴缺失，修正核准依賴後受控續行，未改核心／降參數；原始失敗紀錄保留。
- Phase4A：官方CSD 50英＋50韓、200調性錄音；官方MD5／ZIP CRC／全音訊解碼／MIDI-CSV-phoneme配對通過。schema分song／recording／key；官方en036標題大小寫差異只按ID去重，不改原資料。資料及完整詞只本機保存。64回歸通過，韓文只瀏覽，來源模型相容性待驗證。
- Phase4B：只開已核對CSD_en042a前兩句，2.60–13.65秒。14個音素／MIDI／CSV與波形核對，非假稱人工聽辨；兩版同源同參數，CSD人聲不分離不混音。使用者Terminal隱藏輸入Key，認證兩次400各1請求即停，傳遞測試與離線檢查補齊，未換模型掩蓋問題。
- 正式成功：同Gemini3.5Flash-Lite 3請求／1283tokens。Direct音節[7,10]不押韻；assisted一次修訂後[7,7]押韻通過，但pattern由0.897321降0.733631，兩版pattern不精確。兩份真實YingMusic約11.05秒；Controller耗時17.985／23.192秒，CUDA allocated4.285／reserved5.748GiB。未以工具符合或WAV成功冒充語義／可唱性優劣評分。
- 人工確認：7864兩版中文詞顯示與音訊播放操作驗收通過。收尾只重載，沒有新API／GPU。完整原詞、兩版譯文、API回應、request/result/log與精確WAV路徑留本機ignored資料。
- 最終驗證：73項unittest通過35.989秒；7865暫服及7864實際兩版重載／HTTP SHA一致，CSD英韓、舊EN_01與7863正常，測後關閉自身暫服。原版BLT／lock／pyproject與YingMusic未改，未commit／push。逐次私人Session核對、手動備份及SHA／JSONL驗證完成，身分只記Repo外receipt。
- Phase4C較長片段／整曲及Phase4D操作改善僅有建議，尚未啟動。發布準備只盤點／最小整理，不stage或改寫歷史。

## 2026-10-21T11:56:24+08:00 — Phase4C前安全發布盤點與提交準備

- 人工明確決策：只盤點與最小公開整理、明確提交清單與分支計畫；禁止stage／commit／push／reset／clean／stash／切分支與刪既有成果，不啟動Phase4C，不呼叫Gemini／GPU。
- Git：main HEAD ad565d86e531f64064ed4d93520fde109f5041e5；origin為使用者HW2 Fork；兩次ls-remote確認GitHub main同HEAD／origin main，無遠端新提交，0staged。初2406tracked、6modified／31untracked；整理後7modified／34untracked，共41候選。未發現無關修改，BLT核心／lock／pyproject與YingMusic乾淨。
- 安全：tracked／untracked／ignored狀態及4318個main歷史blob掃描，無獨立憑證格式命中。歷史paper/phase_ablation_results.md有home參照，上游benchmark有既存授權歌詞／trace；單獨報告，不改寫歷史或宣稱整個歷史零歌詞。初寬regex普通字串／套件版本誤判經核對排除，未輸出秘密值。
- 原始保留：37份整理前候選逐檔私人快照、SHA一致，包括完整舊日誌／資源盤點；沒有刪除私人資料。公開README／Context／Decisions／日誌／部分部署文件最小整理，省略內部拓樸／共享權限／其他環境用量。官方14音素常值改為runtime讀官方txt，既有audit／音訊／比較不改。補placeholder manifest與忽略規則，沒有真實本機manifest納入。
- 提交計畫：RELEASE_FILES.json逐檔41路徑，25程式／測試／配置同一完整功能鏈，16公開文件第二筆；app.py及依賴不強拆hunk，避免破壞中間版本。報告附只列印的建議stage／commit指令，沒有執行。Phase4C分支待人工批准新基準節點與遠端同步後才建立。
- 測試：完整本機73項通過35.890秒；只含公開候選的/tmp副本63通過／10官方素材條件skip（共73），35.942秒，無私人artifacts／模型。74 Python AST／4 shell syntax與diff --check通過。
- 原資料：CSD50英文50韓文200錄音重新全verify，1000原檔SHA同舊驗證、2metadata同ZIP、官方ZIP MD5不變；新驗證另存私有位置。7865暫服CSD兩版／全文片段／舊EN_01回播通過且關閉；實際7864英韓、兩版WAV SHA、EN_01與7863正常，沒有重啟既有服務或讀舊Key。0新API／0新GPU／0安裝下載。
- 狀態：可在人工確認新候選清單及既有歷史公開範圍後再stage／commit；Push未授權／未執行，須另批准並重驗遠端／staged安全。完整發布報告與檔案清單已備妥；日誌後核對本次Session並私人備份，驗SHA／JSONL／來源前綴／權限，身分只在Repo外receipt。

## 2026-10-21T16:06:32+08:00 — 人工批准Phase3–4B兩筆正式提交與發布

- 人工明確決策：接受既有上游home參照／授權benchmark歷史，不要求改寫；僅准RELEASE_FILES.json精確41檔，兩筆commit、測試後非force推送自己Fork，SHA一致後建立本機feature/phase4c-full-song，不開始開發。
- 最後gate：主Repo／main／HEAD及GitHub main同ad565d86e531f64064ed4d93520fde109f5041e5，無遠端更新／額外檔案／預先staged。41檔候選安全檢查通過，未納入私人詞／音訊／模型／Session或憑證。
- 已實際完成Commit1：bda86eddebcc759f92ae416725756973412a4e94，feat: integrate YingMusic singing and CSD comparison workflows，精確25檔。逐一核對staged name-status／stat／diff --check與index內容安全，沒有git add .或force-add。
- 本筆文件提交前：第2組只包含原白名單16個公開文件與此已授權日誌更新；再次staged安全檢查後才提交。後續完整回歸、遠端再核對、Push與分支建立尚待此筆提交後依序執行，遇分歧／認證失敗即停。完成SHA與實際結果將保留本機私人release receipt及最終回報，不為自我引用新增第三筆commit或改寫歷史。
- 原始artifacts／CSD／翻譯／WAV／私人快照與既有成果保留。本輪不翻譯、不合成、不下載、不清理資料；Session僅核對本次任務後手動備份，身分與SHA只存Repo外receipt。
