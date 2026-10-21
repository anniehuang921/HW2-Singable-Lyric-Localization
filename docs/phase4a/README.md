# Phase 4A：CSD 資料來源

本階段只匯入、驗證與瀏覽官方資料，不呼叫 Gemini、不執行 GPU 合成。原版 BLT／YingMusic 核心保持不變。

## 來源、授權與保存

來源：[CSD 官方專案](https://github.com/equal-singer/CSD)、[Zenodo 固定記錄 4785016](https://zenodo.org/records/4785016)。官方原始碼版本 `db2502d891c807c76058fc34fbd285c321bf0b8a`。

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)：非商業、姓名標示、相同方式分享；官方 README 另外禁止基於結果貶損原歌者。此授權資訊不代表 HW2 公開 Repo 會重新散布資料。完整歌詞、原始音訊、metadata、譯文、衍生音訊與私人驗證紀錄全部留本機被忽略目錄。

引用：Choi, S., Kim, W., Park, S., Yong, S., & Nam, J. (2020). *Children’s Song Dataset for Singing Voice Research*. ISMIR Late-Breaking/Demo.

本機位置（相對 HW2 Repo）：

- `artifacts/datasets/csd/CSD.zip`：原始 ZIP，1850303574 bytes，官方 MD5 `4c586caff29ca05264cf7223cad1b8a2`。
- `artifacts/datasets/csd/CSD/`：原始解壓資料，3076407592 bytes；兩語言各 501 個檔案，總 1002 個檔案。ZIP 另有目錄項，共 1015 entries。
- 同目錄保存官方 record metadata、原始 README、來源版本、import-receipt、逐檔 SHA-256／解碼驗證與 UI 測試紀錄。不把這些原始內容提交。

ZIP＋解壓檔邏輯大小合計 4.588 GiB；另有少量本機下載暫存／驗證紀錄與選取音訊播放 cache。沒有把資料放 NAS，也沒有刪除其他資料。NAS 的 30 GiB 專案上限維持不變；本機保留至少 10 GiB。

## Adapter 與資料邊界

`hw2_datasets.csd.CSD` 以 metadata 與同 stem 的 WAV／MID／lyric／txt／CSV 建立 Recording。`song_id=CSD_en001`、`recording_id=CSD_en001a` 是不同層級；a／b 是 key_variant，實際半音差取官方 `key_diff`，不假設 a／b 是絕對調名。韓文檔名前綴為 kr，統一語言碼為 ko。

每筆保留完整原始歌詞（包含空行）、標題、長度、音訊路徑、五種配對資料與原始 metadata。`Recording.to_demo()` 可轉既有 Demo 格式，非空歌詞行按原順序提供未來翻譯輸入；這不是已建立的歌詞行時間對齊。CSV 是音節／音符層級時間，不可直接當成整行的時間。

兩種調性是同一歌曲的不同錄音，不能合計成 200 首。即使標題相同也不跨語言自行合併歌曲。

英文留待 Phase 4B 選片段、核對 alignment，再接既有 BLT／Gemini／YingMusic。UI 與事件端均阻擋 CSD 本階段翻譯／合成；韓文翻譯及來源演唱相容性明確標示待驗證。原始錄音可用為未來 melody/timbre 候選，尚未確認整曲或任意片段符合模型限制。

## 啟動與人工驗收

```bash
cd /path/to/HW2-Singable-Lyric-Localization
bash scripts/start_singing_ui.sh
```

使用既有環境與 manifest；不需要 Gemini Key，不做新推論。預設自動讀取 `artifacts/datasets/csd/CSD`，也可用 `HW2_CSD_ROOT` 指定完整資料根目錄。保持綁定 `127.0.0.1:7864`、share=False。若 7864 已有服務，先確認是本案程序再停止該程序，勿動 7863。

VS Code Remote SSH 的 Ports 加入 7864，在本機瀏覽器開啟 forwarding URL。資料來源選 CSD → English／한국어 → 搜尋歌曲 → 在錄音下拉選 a／b → 查看完整歌詞與 metadata → 播放原始演唱。切回 YingMusic Official Demo，選 EN_01 → 載入已保存真實比較 → 選 BLT-assisted → 載入已生成演唱，即可重播既有成果，無需呼叫模型。

## 可重現驗證

已下載 ZIP 的完整性／安全解壓（目的地已存在時拒絕覆寫）：

```bash
python3 scripts/extract_csd.py artifacts/datasets/csd/CSD.zip
.venv-ui/bin/python -m hw2_datasets.verify_csd --output artifacts/datasets/csd/verification.json
PYTHONPATH=.:tests .venv-ui/bin/python -m unittest discover -s tests -v
PYTHONPATH=.:tests .venv-ui/bin/python tests/phase4a_live.py
```

最後一個是明確依賴本機官方 CSD、YingMusic Demo 與既有私人實驗成果的整合測試，暫用 7865、結束關閉；不應當成不依賴資料的公開單元測試。單元測試只用原創合成 fixture，沒有複製官方歌詞。

驗證範圍：官方 MD5、ZIP CRC、檔案配對、逐檔 SHA-256、完整 WAV 解碼／finite／非靜音／44.1k PCM16、MIDI note-on 數與 CSV／音素數一致、音素合法性及序列、CSV 時間落在音訊內。MIDI parser 沒有重建 tempo／音符秒數，不能宣稱已重跑官方全部 MIDI 時間比較；也沒有人工逐字聽辨。

測試結果、資源快照與候選歌曲見 [RESULTS.md](RESULTS.md)。
