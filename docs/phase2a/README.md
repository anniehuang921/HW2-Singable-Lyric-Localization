# Phase 2A — Official Demo Browser

官方來源：[YingMusic-Singer-Plus](https://github.com/ASLP-lab/YingMusic-Singer-Plus)，與主Repo獨立，唯讀。8官方presets：4英4中，Lyric Editing4完整（其中2英文）；Melody Control4缺旋律原詞。12個本機WAV可解碼。音訊與歌詞不隨此Repo散布，須自行合法取得官方素材。

```bash
export HW2_YINGMUSIC_ROOT=/path/to/local/YingMusic-Singer-Plus
.venv-ui/bin/python -m hw2_ui.app --port 7863 --saved-only
```

VS Code Remote SSH的Ports新增7863，再開啟本機轉發網址。服務僅127.0.0.1、share=False。Dropdown可搜尋並依語言／任務篩選，英文優先；原文保留片段邊界，原音訊與不同旋律／timbre分開呈現。

Catalog預設執行時讀本機app_local.py的literal presets，不執行模型程式。可用`--yingmusic-root`覆寫路徑；錯誤路徑會停止啟動，不虛構素材。需要私人快照時：

```bash
.venv-ui/bin/python -m hw2_ui.catalog --output artifacts/catalog/demo_catalog.json
```

素材缺失、非法路徑與音訊解碼失敗有明確原因。不同timbre／melody的ref_text不當原詞，target_text是生成目標。測試分合成離線與依本機官方Repo的整合案例，後者缺來源時skip。瀏覽器聲音聽感及逐段對齊需人工確認。YingMusic演唱尚未實作。
