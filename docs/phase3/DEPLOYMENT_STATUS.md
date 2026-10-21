# Phase 3C — 實際部署與首次中文演唱

時間：2026-10-19T06:55:25+08:00。**EN_01 BLT-assisted一次真實GPU演唱成功，已停止自動推論，待人工聆聽。** 本輪沒有Direct／EN_02、Gemini、改YingMusic／BLT核心、commit或push。

## 環境與實際資源

| 項目 | 驗證結果 |
|---|---|
| GPU | RTX5090，Compute Capability12.0，driver570.211.01 |
| GPU Python | Python3.10.22，獨立`$HOME/.conda/envs/hw2-yingmusic` |
| PyTorch配套 | torch2.7.1+cu128／torchaudio2.7.1+cu128／torchvision0.22.1+cu128；runtime12.8 |
| GPU驗證 | cuda.is_available、sm_120、實際CUDA tensor矩陣運算通過 |
| 依賴 | 原版模型／分離器／中英G2P可用，pip check無衝突；沒有torchcodec0.10 |
| 環境實際占用 | 7.277GiB（低於16GiB上限） |

公開權重／package cache與私人推論資料分開存放；推論暫存只寫本機作業目錄。特定主機掛載、帳號映射與quota盤點保留本機私人紀錄，不隨Repo公開。

## 權重與載入

canonical來源ASLP-lab/YingMusic-Singer-Plus，固定revision`9b3f444f2bccd77fbc03e32eb7c334fc96040b8d`。沒有下載另一套Safetensors或清單外模型。

| 檔案 | 驗證大小bytes | 載入驗證 |
|---|---:|---|
| YingMusicSinger_model.pt | 8,133,498,835 | SHA匹配；ema_model_state_dict，1002 keys |
| stable_audio_2_0_vae_20hz_official.ckpt | 624,569,828 | SHA匹配；state_dict，365 keys |
| model_ckpt_steps_100000_simplified.ckpt | 470,801,253 | SHA匹配；state_dict，634 keys |
| MelBandRoformer.ckpt | 913,106,900 | SHA匹配；官方分離器GPU載入成功 |
| 分離器YAML | 1,721 | 固定revision、size驗證，SHA記公開provenance |

合計10,141,978,537bytes＝9.4455GiB，NAS單份保存。公用provenance不含歌詞／Token，本機manifest／完整環境freeze與安裝／驗證log存artifacts/deployment/。模型YAML、VAE JSON及既有G2P ONNX／字典來自唯讀本機官方Repo。

主模型首次獨立載入12.41秒、CUDA peak allocated約2.72GiB。補齊分離器動態依賴後又驗證分離器＋主模型均載入成功，才受控接續演唱；沒有變更權重、架構或品質參數。

## 一次真實成功的結果

- 資料來源：本機Phase2B正式保存比較，非把Prompt重寫當新資料；source／segment IDs／reference text與正確音訊SHA核對，兩段目標[8,6]。繁體原文保留，只有推論副本轉簡體。
- 參數：Seed666、NFE32、CFG3、t_shift0.5、sil_len_to_end0.5；原音訊同時作正確melody／timbre reference。分離一次共用同源stem，合成人聲後混回對應伴奏。
- 作業總耗時 **23.656秒**；worker內分離1.872秒、模型載入11.347秒、聲學合成3.108秒。
- PyTorch CUDA peak allocated **4.228GiB**、reserved **4.559GiB**。這是allocator峰值，不是整卡NVML連續採樣峰值；沒有OOM或競爭中的GPU compute job。
- WAV：44,100Hz、雙聲道、376,168frames、8.529887秒；有限值、非靜音，peak0.46734、RMS0.07380。SHA-256與HTTP下載一致，且不同於所有原始輸入音訊SHA；原版model forward實際執行，沒有將原曲或Mock當生成。
- WAV及request.json／result.json／worker.log／metrics.json／分離stem全在本機`artifacts/singing/<run-id>/`，精確位置記本機artifacts/deployment/en01-final-result.json，不提交Git或放NAS。
- 全部worker log僅1份SYNTHESIS_SUCCESS。一次較早的啟動在動態import缺beartype時失敗，尚未分離／聲學合成；記錄保留。一般依賴修正後受控續行1次成功，不做無限制重試、不自動Direct／EN_02。

## 必要小修正與實際錯誤

- 套件用獨立overlay，未照裝上游互斥torch2.6／torchcodec0.10，未改第三方requirements。
- 分離器constructor才動態import beartype；補上子專案指定beartype0.14.1。原版聲學／分離程式不改，未降參數。
- 安裝監控初版遇du快取檔瞬時消失／NFS掃描延遲，曾中斷安裝；修正量測重試後，使用現有cache離線完成PyTorch。沒有觸及實際30GiB／16GiB／10GiB資源限制。權重下載前保留9.5GiB，下載後監控門檻含已占用權重，不把預留再次加算。
- Worker增加load-only階段、耗時／CUDA allocator統計、本機私人TMP與離線HF cache；使用現有原版class，沒有新推論架構。
- UI新增已生成音訊讀取，核對Demo、候選、文字、模型revision、輸入hash與輸出hash。避免為瀏覽重新耗GPU。

## UI與測試

- 只核對自己主Repo cwd／owner／argv後重啟7864。未讀任何舊程序Key或environ，7863未中斷。
- 7864實際選EN_01→載入真實比較→載入已生成BLT-assisted音訊；HTTP200、Range206、解碼44.1kHz雙聲道通過，原英文音訊HTTP200。Direct／人工音訊仍空白。
- 最終單元／回歸 **55項通過**（35.029秒）；Adapter聚焦8項通過；pip check無衝突。音訊回播驗證new_inference_calls=0、new_gemini_calls=0。
- 先前13份正式比較／編輯原檔仍與私人備份SHA一致；BLT核心／pyproject／lock／Phase2B演算法與YingMusic Repo未修改。未重新跑完整Baseline CLI，原工具回歸包含於既有測試。
- 警告：原版PyTorch AMP／Pydantic deprecation warnings仍有，FlashAttention外部套件未安裝，模型沿用原版torch attention可正常執行。這不代表未來所有依賴版本皆相容，實際freeze本機保留。

**人工驗收：** 依README的7864操作按「載入已生成演唱」，聆聽中文與原英文；音準、清晰度、旋律保留、自然度及可唱性尚待人工，不因解碼與音節符合就宣稱品質合格。成功後已停止自動推論。
