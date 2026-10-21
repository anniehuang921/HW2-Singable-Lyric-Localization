# Phase 3：公開模型與環境規劃

原調查日期2026-10-19；此發布版保留官方來源、權重大小與相容性證據，不公開主機磁碟拓樸、共享目錄權限、其他研究環境用量或私有掛載位置。完整原始調查已逐檔備份於本機ignored私人整理快照，沒有刪除原始紀錄。部署已成功，歷史規劃不代表目前仍被阻擋。

## 3. 官方來源、版本與精確檔案大小

本機YingMusic原始碼revision：`baa409c2e7e5e775f09b4e92a220808f4827d2cc`。官方模型canonical ID為 **ASLP-lab/YingMusic-Singer-Plus**。

本次小型[HF API metadata](https://huggingface.co/api/models/ASLP-lab/YingMusic-Singer-Plus?blobs=true)取得revision **9b3f444f2bccd77fbc03e32eb7c334fc96040b8d**，下表bytes均來自該revision的size／LFS metadata，非估計、非本機下載量。GB為十進位，GiB為2^30 bytes。

重要交叉核對：舊ID的[API](https://huggingface.co/api/models/ASLP-lab/YingMusic-Singer?blobs=true)目前回HTTP307指向Plus；follow redirect後id、revision及5個大檔SHA-256與Plus相同。這只證明**本次查詢版本**是同一份來源，不表示任意歷史Plus／非Plus checkpoint都相容。部署仍應pin canonical ID、revision與SHA，不依賴可變的舊別名。

| Component | Model Source／檔案 | Version | File Format | Download Size（bytes；約GiB） | Required / Optional | Notes |
|---|---|---|---|---:|---|---|
| Hub完整模型序列化 | Plus/model.safetensors | 上述HF revision | Safetensors，API列727,469,236個F32參數 | 2,910,134,776；2.710GiB | Hub載入路徑必需；與raw路徑二選一 | 不可改名為EMA .pt給目前Adapter |
| 原始模型checkpoint | Plus/ckpts/YingMusicSinger_model.pt | 同revision | PyTorch .pt | 8,133,498,835；7.575GiB | 目前Adapter路徑必需 | 官方建構子預設讀ema_model_state_dict；本輪未下載驗證內部keys／optimizer內容 |
| Stable Audio VAE | Plus/ckpts/stable_audio_2_0_vae_20hz_official.ckpt | 同revision | PyTorch .ckpt | 624,569,828；0.582GiB | VAE功能必需；raw路徑需此獨立檔 | Hub整包路徑不應先重複下載 |
| MIDI teacher | Plus/ckpts/model_ckpt_steps_100000_simplified.ckpt | 同revision | PyTorch .ckpt | 470,801,253；0.438GiB | MIDI功能必需；raw路徑需此獨立檔 | 不能直接省略teacher改聲學路徑 |
| Vocal separator | Plus/ckpts/MelBandRoformer.ckpt | 同revision | PyTorch .ckpt | 913,106,900；0.850GiB | 含伴奏輸入需要；純人聲可選 | EN_01官方preset開啟分離，應保守納入 |
| Separator設定 | Plus/ckpts/config_vocals_mel_band_roformer_kj.yaml | 同revision | YAML | 1,721 | 使用分離器時必需 | 與checkpoint配對 |
| Hub設定 | Plus/config.json | 同revision | JSON | 209 | Hub路徑必需 | 指向模型YAML／VAE JSON，未指定獨立ckpt_path |
| 模型與VAE架構設定 | 官方Git src/YingMusicSinger/config/ | 本機Git revision | YAML／JSON | 已有本機檔，無新增下載 | 必需 | 不把設定檔當訓練權重 |
| 中文G2P | 官方Git內g2p sources | 本機Git revision | ONNX、BERT vocab/config、字典 | 已存在；本輪新增下載0 | 必需 | 存在不等於依賴已能載入；不讀其他專案模型替代 |

精確檔案列表可在[官方模型根目錄](https://huggingface.co/ASLP-lab/YingMusic-Singer-Plus/tree/9b3f444f2bccd77fbc03e32eb7c334fc96040b8d)及[ckpts目錄](https://huggingface.co/ASLP-lab/YingMusic-Singer-Plus/tree/9b3f444f2bccd77fbc03e32eb7c334fc96040b8d/ckpts)核對。

### 3.1 同一模型的兩條載入路徑，不可重複計價

- **目前HW2 Adapter：raw建構子路徑。** `YingMusicSinger(...)`依次建立主模型／VAE／MIDI，再分別載入本機checkpoint。4個權重＋separator YAML共 **10,141,978,537 bytes＝9.4455GiB**。不需要再下載model.safetensors。
- **官方Hub路徑：** `YingMusicSinger.from_pretrained(本機Plus snapshot)`，Hub config不指定raw checkpoint，PyTorchModelHubMixin載入整個module的Safetensors。官方Mixin的[保存／載入原始碼](https://github.com/huggingface/huggingface_hub/blob/v0.35.3/src/huggingface_hub/hub_mixin.py)對整個module序列化，故VAE／MIDI在此是模型子模組，不應再加一套raw檔作預設需求。Safetensors＋分離器＋兩設定合計 **3,823,243,606 bytes＝3.5607GiB**。本輪沒有讀tensor keys／strict-load驗證，整包完整性仍待部署時確認；不能把它宣稱為已實跑方案。
- **現有Adapter不能直接走Hub分支。** 它要求EMA .pt與個別VAE／MIDI檔。若選較小的Hub套件，後續須另外批准最小loader適配與strict missing/unexpected keys檢查；這不是修改聲學模型。本輪沒有更改Adapter。
- 不建議snapshot_download整個13.1GB模型Repo；它同時含兩種序列化，會把不需要的另一套也下載。用精確allow-list固定revision，保留單一權重儲存位置。HF cache本身就是權重位置，不能再把同一份權重加一次作cache需求。

## 4. EN_01最小測試與完整方案

原始碼證據以本機`infer_api.py`、`initialization.py`、`app_local.py`、`src/YingMusicSinger/infer/YingMusicSinger.py`及模型YAML為準；官方[Repo](https://github.com/ASLP-lab/YingMusic-Singer-Plus)供交叉查閱。

| 元件／步驟 | A 最小測試 | B 完整官方流程 | 原始碼依據／限制 |
|---|---|---|---|
| 主聲學模型 | 必需 | 必需 | forward呼叫model.sample |
| Stable Audio VAE | 必需 | 必需 | prepare_input encode_audio，forward decode_audio；不能省略 |
| MIDI teacher | 必需 | 必需 | 本機YAML melody_input_source為some_pretrain_fuzzdisturb；prepare_input需teacher、forward assert midi_p/bound_p非空；改來源會進NotImplementedError |
| Vocal separation | 純人聲才可省 | 含伴奏時使用 | README要求pure vocals；CLI的separate_vocals是可選前處理，不是聲學核心 |
| EN_01現有來源 | 本次保守納入分離 | 分離後再處理 | 官方preset separate=true、mix=true；8.529875秒、48kHz、雙聲道。沒有獨立已驗證純人聲檔或官方純人聲證明，不能把原WAV當純人聲 |
| 伴奏混音 | 可先省，先驗收中文乾聲 | 生成後混回 | CLI只有separate且mix旗標才混音；模型forward已回傳可播放聲音 |
| EN_02、批次、多GPU、訓練 | 延後 | 另階段 | EN_01單例不需要 |

目前HW2 Adapter為公平比較固定分離＋混音，並拒絕略過分離；即使官方CLI允許略過混音，本輪也不自行改Adapter設定。若人工同意「先乾聲」，之後可用既有Settings的mix_accompaniment=False（不變聲學模型）；須兩候選同設定並記錄。

純人聲方案只能在提供合法、與原旋律／reference text對應且已確認的vocal stem後成立；不能用免費資源之名換成另一首Demo。對目前EN_01，**最小保守下載仍含MelBandRoformer**。

禁止直接import app_local.py：它eager download_files並載模型與分離器。infer_api.py雖lazy，get_model仍先呼叫download_files，而且舊ID目前依賴轉址。initialization task=infer只列分離器與YAML，不代表只有這兩個檔案就是完整推論需求；主模型由from_pretrained另行取得。

## 5. RTX 5090：建議隔離的cu128方案

[NVIDIA官方表](https://developer.nvidia.com/cuda/gpus)列RTX5090為 **Compute Capability 12.0（sm_120）**。[PyTorch 2.7 release](https://pytorch.org/blog/pytorch-2-7/)開始提供Blackwell支援及CUDA12.8 wheels。原requirements的torch2.6.0官方輪子列cu118／cu124／cu126，不能當作5090已支援的配置。

建議先試 **Python3.10＋torch2.7.1/cu128＋torchaudio2.7.1＋torchvision0.22.1**（version pair見[官方previous versions](https://pytorch.org/get-started/previous-versions/)）。這是接近上游2.6、無需升級系統driver的受控候選，不是已驗證相容環境。Python3.10符合YingMusic README與這套wheel；不建議使用本機系統Python3.13混裝。

Driver570.211.01高於CUDA12.8 GA在Linux的570.26門檻，見[NVIDIA release notes](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html)。nvidia-smi的12.8不是Toolkit／PyTorch runtime安裝證據；本輪未找到nvcc，現有UI／BLT環境無torch。預編譯PyTorch wheels會帶相應runtime依賴，沒有編譯擴充需求時不先安裝整套Toolkit，不動系統driver。

### 已確認的依賴矛盾與未確認事項

- 官方requirements同時鎖torch2.6.0與torchcodec0.10.0。依[TorchCodec官方相容表](https://github.com/meta-pytorch/torchcodec#compatibility-with-torch-versions)，0.10配torch2.10，0.3–0.5配torch2.7；原列表本身不是可直接採用的一致鎖檔。
- 本機此推論路徑未發現直接import torchcodec；torchaudio2.7讀WAV不應為此先加入0.10。部署應先確認匯入閉包，無需則不安裝；若真的需要，選相容版本後重新解析。不是用constraint強壓互相衝突的exact pins。
- torch／torchaudio／torchvision必須整組替換，不能只升torch。禁止直接`pip install -r`把官方2.6又覆蓋回來；未來在HW2獨立overlay requirements處理，不改第三方原檔。
- transformers4.57.6、tokenizers、peft、diffusers、lightning、bitsandbytes、torchcrepe、Stable Audio相關套件與NumPy／librosa／numba的實際匯入及binary ABI相容性**尚未執行resolver／import測試**；不能宣稱全requirements已解決。
- 訓練／批次／評估套件不全是單例必需，但部分可能被頂層import帶入。最小環境須從實際import閉包逐步驗證，不能無依據排除依賴。
- 若2.7.1路徑被依賴阻擋，另一候選是torch2.10/cu128＋torchaudio2.10＋torchvision0.25及torchcodec0.10；API差異更大，不作自動fallback，須再核對原版音訊I/O。不要自動選最新版cu130而導致driver升級。

部署後才可檢查torch.version.cuda、get_device_capability==(12,0)、get_arch_list含sm_120、短矩陣運算、torchaudio WAV I/O與必要套件import；本輪未執行GPU測試。


## 空間與隔離原則

目前raw權重共9.4455GiB，Python／PyTorch／CUDA環境另計；保留單份權重，避免Hub／raw重複下載。部署空間請自行量測並保留暫存與輸出餘量，實際峰值不是只看權重大小。專案既有界線為NAS公開模型／cache最多30GiB，本機至少10GiB可用；這不是其他機器可用容量保證。

實際manifest只放ignored artifacts，使用絕對路徑指向經核對本機權重；公開[manifest.example.json](manifest.example.json)只有placeholder。原詞、譯文、生成音訊、Token、Session與私人log不放共享模型cache。

## 附錄：固定版本的大檔SHA-256（官方LFS metadata，未下載檔案）

| 檔案 | SHA-256 |
|---|---|
| ckpts/MelBandRoformer.ckpt | `87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e` |
| ckpts/YingMusicSinger_model.pt | `8b0684557abcdb00ee9e39cb351d5b9b90b98773ab6630d00fa27daa0e51ab56` |
| ckpts/model_ckpt_steps_100000_simplified.ckpt | `aa710fce920b4dae281b0e6cc2acba83345d82ee62d51f7bafeb29636f28f97c` |
| ckpts/stable_audio_2_0_vae_20hz_official.ckpt | `dc2c4a8ec9731594951a27eff4a188a89b82859649c341c51d050101d1ce0b39` |
| model.safetensors | `b32dc225a6cfff37f2252b7d3b60cbf536f656de349eba6d5b773aa5f5b780e4` |
