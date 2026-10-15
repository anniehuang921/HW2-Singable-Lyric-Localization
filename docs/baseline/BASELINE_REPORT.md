# Phase 1 — Original BLT Baseline

環境：隔離 hw2-blt，Python3.11、uv；核心依賴依原uv.lock，未修改演算法。

重現（不要自動安裝系統工具）：

```bash
export HW2_BLT_PYTHON="$HOME/.conda/envs/hw2-blt/bin/python"
"$HW2_BLT_PYTHON" docs/baseline/run_baseline.py --out /tmp/hw2-baseline.json
"$HW2_BLT_PYTHON" docs/baseline/run_api_probes.py
```

21 CLI案例：16符合預期、4觀察、1既知中文尾端標點押韻失敗，所有程式exit0。合成輸入與實際命令在runner中；該runner的case狀態需要檢查，不以exit0宣稱全數通過。額外12API probes已執行。公開統計見public-summary.json。

原版限制：中文韻尾不去標點；digits可被接受；validator行數不符時feedback與旗標可能矛盾；空列表韻式為A。完整新的模型翻譯不屬此Baseline成功條件。既有上游100筆重評96非空，不是本次生成；相關dataset沿用上游既有授權，未新增公開原詞或完整譯文。

原始環境／命令輸出與初始失敗紀錄本機保留；公開版不包含私人主機或環境清單。不安裝CLT／ClaudeCLI／Modal或下載模型。
