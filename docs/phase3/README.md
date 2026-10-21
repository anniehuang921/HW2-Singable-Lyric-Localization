# Phase 3 — YingMusic 真實演唱

2026-10-19：EN_01 BLT-assisted已完成一次真實本機GPU演唱。沒有重新翻譯／Gemini呼叫；Direct與EN_02沒有合成。完整原詞、繁體譯文、提交簡體副本、音訊與request/result/log只在本機artifacts/singing/，不提交Git。

## 現在聆聽

7864已運行新版同一Gradio UI；7863保留原檢閱服務。

1. VS Code Remote SSH的Ports新增7864，開啟轉發的本機網址。
2. Dropdown選SingEdit_EN_01，按「載入已保存的真實比較」。
3. 演唱來源選BLT-assisted，按「載入已生成演唱（不重新推論）」。
4. 播放BLT-assisted中文演唱，與上方原英文音訊比較。Direct／人工版未生成，保持空白。

載入播放器不使用GPU或API。暫不再按生成；此次自動推論已停止，待人工驗收音準、旋律保留、歌詞清晰與自然度。音訊非靜音、音節符合與流程通過都不等於品質已合格。

## 重啟與配置

若需重啟7864，先在該服務自己的Terminal停止，再執行：

```bash
bash scripts/start_singing_ui.sh
```

腳本沿用`.venv-ui`跑UI、獨立`$HOME/.conda/envs/hw2-yingmusic/bin/python`跑worker；本機`artifacts/deployment/singing-manifest.json`已具真實驗證路徑。沒有Key輸入，也不重新短測或翻譯。服務只127.0.0.1，不share，不接觸7863。

worker只調唯讀官方模型class；不import eager-download app或下載初始化入口。固定Seed666／32steps／CFG3／t_shift0.5，分離人聲後合成、混回伴奏；同一原音訊的reference／melody／timbre映射及片段ID已核對。繁體原詞不覆寫，只有推論副本t2s並以|分段。

NAS只存公開權重／套件cache及非私人安裝暫存，不假設使用者隔離；推論TMPDIR／XDG／HF離線cache強制在本機作業目錄。原始詞、翻譯、worker log、生成音訊及任何憑證不放NAS。

實際版本、下載大小、耗時、VRAM與限制見[DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)。規劃歷史見[STORAGE_AND_MODEL_PLAN.md](STORAGE_AND_MODEL_PLAN.md)。原ENVIRONMENT.md是部署前快照，不能當目前尚缺權重的結論。

## 驗證

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-ui/bin/python -m unittest discover -s tests -v
```

最終55項通過。7864實際載入真實比較及已生成WAV，HTTP200／Range206／解碼／非靜音通過，沒有新推論。Mock仍明確audio=null，不當作真實成果。人工修改可再次驗證；是否重新合成由人工決定，本輪不自動生成其他版本。

## 可公開的部署配置範例

此Repo不提供權重或本機環境。準備合法取得的唯讀官方Repo、固定revision權重及足夠GPU／磁碟後，可在獨立環境安裝已驗證配套（以下為操作說明，不會自動執行）：

```bash
conda create -n hw2-yingmusic python=3.10
export GPU_PYTHON="$HOME/.conda/envs/hw2-yingmusic/bin/python"
uv pip install --python "$GPU_PYTHON" torch==2.7.1 torchaudio==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python "$GPU_PYTHON" -r docs/phase3/gpu-requirements.txt
```

以[manifest.example.json](manifest.example.json)為欄位範本，逐一填入核對過的本機絕對路徑，另存 `artifacts/deployment/singing-manifest.json`。不把範例placeholder視為已安裝；不把真實本機manifest提交。公開權重來源與SHA見[模型規劃](STORAGE_AND_MODEL_PLAN.md)，G2P／模型設定沿唯讀官方Repo。軟體不自動下載缺失權重，配置未就緒會報錯。Conda／GPU驅動須由操作者事先準備，實測配套不保證其他硬體或未來套件組合。
