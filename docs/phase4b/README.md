# Phase 4B：CSD 首次中文翻唱

目前狀態：**兩版真實翻譯與中文演唱成功，使用者操作／播放驗收通過**。完整統計、回播操作與後續建議見 [RESULTS.md](RESULTS.md)；完整歌詞與音訊僅保留本機。以下安全執行流程及未就緒描述為開發過程紀錄，既有結果請優先載入，不需重跑。

## 已完成的來源核對

只開放 `CSD_en042a`，Twinkle Twinkle Little Star，官方前兩個歌詞行，原 BLT 音節為7、7。完整原文、音素與核對紀錄只存被忽略的 `artifacts/datasets/csd/excerpts/`。

不是只按音節數選片段：逐一核對14個官方音素與前兩行文字、MIDI音高／onset／offset與CSV，最大時間差0.000048秒；下一句開始14.1176秒。實際解碼原音檢查波形能量，保留首音前餘量及最後母音釋放，避開下一句前的換氣，正式裁切 **2.60–13.65秒**，44100Hz／487305frames／11.05秒。初次13.85秒候選另外保留，未破壞或覆寫官方原音。

這是官方標註、音素與波形核對，不是假稱已人工聽辨。最終逐字聽感、邊界是否自然仍待使用者驗收。官方README將wav定義為vocal recording，錄於隔音室；本方案直接使用其人聲軌，不聲稱已人工排除所有背景串音，不額外分離或虛構伴奏。

## 安全執行

在 Remote SSH Terminal 執行，**不要把 Key 貼進對話**：

```bash
cd /path/to/HW2-Singable-Lyric-Localization
bash scripts/start_csd_phase4b.sh
```

腳本隱藏輸入Key，僅存程序環境，不寫檔／argv／日誌，不讀其他程序憑證。沿用gemini-3.5-flash-lite／現有OpenAI-compatible Provider／Free Tier；temperature沿用現有預設0.2、4096tokens、reasoning_effort low、45秒timeout。最多Direct1＋assisted3次，無新短測、不自動重試；API或模型錯誤即停止。不重新下載權重，不新增環境，不操作Billing。

只針對這份已核對片段執行原版BLT工具與既有Direct／assisted流程。Direct保留原始回應與既有s2t正規化，不為符合音節重寫；assisted最多2次修訂。私有比較保存在既有 `artifacts/translations/`，另於 `artifacts/phase4b/experiment-*.json`彙整原文、譯文、每次驗證、原比較請求數、本輪新增請求數與usage（若API提供）。若失敗則保存停止原因，不繼續推論。

翻譯成功後依序生成assisted、Direct各一份，沿用原Worker與固定模型manifest，音訊及結果留 `artifacts/singing/<run-id>/`。兩者固定同一片段、reference文字、seed666／NFE32／CFG3／t_shift0.5／sil_len_to_end0.5；純人聲不分離、不混音。推論副本轉簡體，原繁體不覆寫。保存完整設定、耗時、CUDA allocator峰值（不是整卡NVML峰值），WAV解碼／非靜音／長度檢查。Direct太長或失敗則如實保留，禁止縮短歌詞再假稱相同比較。

所有正式結果成功後，腳本只停止核對owner／cwd／argv的本案7864並啟動新UI，7863不動。不需要再輸入Key或重做短測；既有結果可重載，重複按翻譯或正式候選生成會優先返回相同片段版本的已保存結果，不反覆耗費API／GPU。失敗時不自動切模型／重試／替換服務，請保留Terminal錯誤並回報。

## UI 與驗證

VS Code轉發7864 → CSD → English → Twinkle… → a。

上方保留完整原曲與歌詞；新增「已核對片段」兩行原文與11.05秒播放器。翻譯／演唱使用片段，不會把整首送給模型。可按開始翻譯或載入比較，選Direct／assisted、生成或載入已生成演唱。人工編輯功能保留，不列入正式兩版比較；其他CSD錄音／韓文仍只瀏覽。舊EN_01原音／比較／已生成演唱照常回播。

實測：70項單元回歸通過35.884秒；最後片段版本綁定等小修改後6項聚焦測試再次通過。新增皆原創合成fixture，沒有官方歌詞或假演唱。`tests/phase4b_live.py`在7865暫服，驗證全文／片段分離、HTTP200／解碼、487305frames與舊EN_01演唱回播，0API／0GPU；完成關閉7865。當下尚無正式CSD結果，測試紀錄明確為saved_csd_results=false。未宣稱兩版中文WAV已通過。

```bash
PYTHONPATH=.:tests .venv-ui/bin/python -m unittest discover -s tests -v
PYTHONPATH=.:tests .venv-ui/bin/python tests/phase4b_live.py
```

完成真實實驗後需再確認7864三份片段音訊、兩版驗證／usage／耗時與VRAM、韓文資料庫及7863，才提交人工聆聽。機器成功不等於翻譯自然、語義正確或演唱品質合格。不進入Phase4C、不批次處理其他歌曲。

後續兩次真實啟動均在Direct遇HTTP400／INVALID_ARGUMENT「Please pass a valid API key」，各1請求，尚無CSD中文結果。離線根因、傳遞測試與最小診斷修復見[TRANSLATION_FAILURE_DIAGNOSIS.md](TRANSLATION_FAILURE_DIAGNOSIS.md)。安全腳本現會在Python確認非空／無引號空白；這不是Google有效性驗證，仍需使用有效Key，禁止自動反覆重試。
