# Phase 4A 實測結果

時間：2026-10-21，Asia/Taipei。沒有 Gemini 請求、GPU 合成、套件安裝、模型下載、commit 或 push。

## 完整資料與資源

| 語言 | 歌曲 | 調性錄音 | 原始配對檔案 |
|---|---:|---:|---:|
| English | 50 | 100 | 每錄音 WAV／MID／lyric／txt／CSV |
| Korean | 50 | 100 | 同上 |
| 合計 | 100 | 200 | 1000 個錄音相關檔案＋2 個 metadata.json |

官方 [Zenodo 記錄](https://zenodo.org/records/4785016) 提供 CSD.zip，1850303574 bytes；官方 MD5 核對通過。ZIP 中央目錄解壓大小3076407592 bytes、1015 entries，全部 CRC 通過。保留原 ZIP 與解壓後原始位元組。

本機計算 ZIP SHA-256（不是官方額外公布的 hash）：`85fa62ad41b9a035048e588004be9d8c7b48b1a4c8b7763491a3afab2ef40589`。

- 資料：Repo 本機 `artifacts/datasets/csd/`，被 Git 忽略；占用快照4944723968 bytes，約4.605 GiB（含 ZIP、解壓、初次下載暫存與驗證紀錄）。所有原始資料留本機，沒有放 NAS。
- 網路單連線下載較慢，改用有上限的12連線分段下載，完成後合併且移除本輪分段暫存。未刪其他資料；沒有改動模型／環境。

## 自動化驗證

1. `scripts/extract_csd.py`：官方大小／MD5、全部 ZIP CRC、路徑／symlink 防護、本機餘量、安全解壓與拒絕覆寫。
2. `python -m hw2_datasets.verify_csd ...`：200/200 WAV 全長解碼，44.1kHz PCM16、有限值、非靜音；1000個配對檔案均計算 SHA-256。200/200 MIDI note-on 數＝CSV 行數＝音素 syllable 數；CSV／txt音素序列、音素集合、pitch／時間範圍均通過。200錄音總長17502.775秒。
3. `PYTHONPATH=.:tests .venv-ui/bin/python -m unittest discover -s tests -v`：64項通過，36.179秒；包括9項新增 CSD 測試、原 BLT 工具、Phase2 UI／翻譯／儲存及Phase3 Adapter回歸。所有新增fixture為原創合成資料。
4. `tests/phase4a_live.py`：7865暫時服務；CSD英文 en042 a／b、韓文 kr001 a／b，歌詞逐字與原檔相同、metadata對應正確，HTTP200／Range206／解碼通過；切回官方 EN_01，原音訊、既有真實比較與中文演唱回播通過。事件端直接要求 CSD 翻譯／合成也會拒絕；測試的 Provider／生成方法設為禁止呼叫。結束關閉7865。
5. 實際7864：重新啟動前只核對本案程序 owner／cwd／argv，沒有讀舊程序環境或Key。en038b選歌、metadata／音訊HTTP200／44.1k解碼成功；原EN_01真實比較與已生成演唱HTTP200。只監聽127.0.0.1。7863仍HTTP200。
6. `git diff --check`通過；BLT核心、鎖檔、翻譯模組未變；唯讀YingMusic仍乾淨。原資料、完整詞／metadata與所有私人測試JSON均被Git忽略。

初次資料載入發現官方en036a標題首字大寫、en036b首字小寫。Adapter按穩定song_id去重，以不區分大小寫核對同曲名稱，保留每份原metadata；已補回歸測試，仍是50首英文。另一次UI測試在韓文選單狀態直接提交英文ID，被Gradio正確拒絕；測試改為先切回英文選項後通過，沒有放寬選項驗證。

## Phase 4B 候選（尚未執行翻譯或合成）

以下前兩個非空歌詞行已實際送原版BLT分析音節；表中CSV候選時間，僅以音節數對應前N個音符提出，**尚未人工驗證行／音符對齊**，不能當成已完成裁切。後續應聽原音、核對首尾及靜音邊界，再決定裁切範圍與reference文字。

| 錄音 | 官方標題 | 兩行BLT音節 | 建議CSV音符／時間 | 選擇理由 |
|---|---|---|---|---|
| CSD_en029a | Mary had a little lamb | 7、6 | 1–13；3.1533–9.1883秒 | 約6秒的兩句、重複結構，接近既有兩片段驗證方式；可觀察非等長中文行是否套入旋律。 |
| CSD_en038a | Row row row your boat | 5、5 | 1–10；2.4000–6.6875秒 | 短小、兩行等音節，適合作為最小控制案例；較短中文譯句的語義濃縮仍需人工判斷。 |
| CSD_en042a | Twinkle twinkle little star | 7、7 | 1–14；2.8235–13.5000秒 | 兩句規整且較完整，適合固定音節／韻腳比較；約10.7秒候選片段便於聽感評估。 |

a為官方key_diff=0候選；對應b錄音也已完整保留。選哪個key、時間邊界與英文reference需由人工確認，本輪沒有自動比較或合成。

## 尚待人工驗收

- 在本機瀏覽器經VS Code轉發7864，選CSD→語言→歌曲→a／b，確認播放器實際出聲與歌詞聽感對應。
- 確認三首候選與短片段；逐字對齊、語義／翻譯品質與中文可唱性尚未評分。
- 韓文僅完整導入／播放；翻譯與YingMusic來源演唱相容性未驗證。
- 本次未逐份經瀏覽器測200錄音，也未重建MIDI tempo秒數驗證。全200音訊的程式全長解碼及配對檢查已通過，與人工聽辨是不同驗收。

本輪停止於Phase4A，等待素材／UI驗收，不進入Phase4B。
