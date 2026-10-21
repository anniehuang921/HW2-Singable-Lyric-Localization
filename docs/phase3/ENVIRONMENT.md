# Phase 3 — Measured Environment and Blockers

盤點日期2026-10-16 Asia/Taipei。只讀原始碼／套件metadata與GPU狀態，不import app_local、infer_api或模型。

|項目|實際結果|
|---|---|
|GPU|NVIDIA GeForce RTX 5090，32607MiB總量，32099MiB空閒（當時快照）|
|Driver|570.211.01|
|CUDA|nvidia-smi顯示驅動支援12.8；未找到nvcc，未確認Toolkit或PyTorch CUDA runtime|
|Python|UI／hw2-blt 3.11.17；系統預設3.13.2|
|PyTorch／torchaudio|上述環境metadata未安裝；沒有可用專用YingMusic .venv|
|官方建議|README Python3.10；requirements torch2.6.0、torchaudio2.6.0、torchvision0.21.0及大量音訊／ML套件|
|權重|官方Repo無ckpts；已檢查標準HF cache未找到ASLP目標模型。其他專案cache不作本案權重使用|
|G2P|官方Repo內有BERT tokenizer vocab／ONNX與字典檔；未執行相容性驗證|
|磁碟|主工作磁碟僅約1.8GiB可用，容量已近滿；未刪除其他資料|

## 需求與成本邊界

需要主模型Plus相容權重、Stable Audio VAE、MIDI teacher、MelBandRoformer與分離器yaml，以及相容的獨立GPU Python環境。不能假設非Plus初始化檔等於Plus模型。需先查核權重manifest／檔案大小，再批准下載；本輪未下載任何權重。

GPU雖約32GiB可用，尚無真實峰值VRAM／耗時數據，不能宣稱足夠或推估已達效能。RTX5090的實際PyTorch CUDA build相容性須驗證，不能直接假定官方2.6鎖定輪子適用。UI與Baseline環境保持不變。

工程規劃暫預留至少30GiB獨立磁碟空間供GPU環境、權重與暫存（**規劃估計，不是權重清單實測**）；現有1.8GiB不適合開始。實際需要多少取決於checkpoint格式、重複Hub cache與CUDA套件，取得檔案清單後才能精確報價。先由使用者決定可用磁碟與環境／下載授權，不自行清理其他專案或建立大型環境。

原版支援中文／英文統一tokenizer與跨語言target text（程式契約）；英文演唱轉中文效果本輪未實測。README明確要求pure vocals，含伴奏音訊應先分離。官方preset分離旗標只是線索，不能只由檔名證明音訊純度；EN_01公平比較預設兩模式都先分離再混回同伴奏。人工聽感判斷尚未完成。

Adapter與UI完成並可驗證缺失處理；EN_01／EN_02本輪沒有生成中文演唱，不存在可交付的真實singing.wav。阻礙為權重／環境／磁碟空間；不是LLM或翻譯流程問題。
