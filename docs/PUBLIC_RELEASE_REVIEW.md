# Public Release Review

2026-10-16（Asia/Taipei）。使用者已批准清理及僅未公開歷史重整。

公開：程式、合成測試、方法與工程摘要、不含歌詞的Baseline／真實翻譯數值。排除：官方Catalog快照、完整原詞／譯文、原始實驗JSON、私人環境、原始Session與備份。歷史原文件保存在本機artifacts/private-release與Repo外完整驗證備份。

先fetch確認遠端為原初始化父commit、沒有遠端分支引用初始化，再建立並驗證完整bundle與2458份工作檔快照。公開main將從原遠端父commit建立新階段commits，保留上游所有歷史，不force push。舊本機commit保留於私人bundle。

原授權疑慮處理：不主張YingMusic範例歌曲再散布權；UI執行時讀本機已合法取得的官方Repo，不散布音訊／原詞。完整翻譯與每次修訂仍可本機讀取，不以刪除實驗解決公開問題。

本輪沒有新API、模型下載、Billing或演算法修改。公開測試以合成輸入驗證工程流程；原素材與真實結果整合測試依本機條件執行。完成測試／history與staged掃描後才Push，遠端更新即停止。

最終狀態：安全清理、完整備份、47本機單元測試及乾淨公開目錄37通過／10條件skip均完成。Push已嘗試，但Server缺可用GitHub HTTPS／SSH認證，遠端未修改。需要使用者於自己的Terminal提供GitHub認證；勿將token放入對話／URL／命令列或檔案。

## 2026-10-21：Phase3–4B發布準備（未提交）

遠端main與本機HEAD一致，無staged變更。本輪補齊公開README／manifest範例／忽略規則，原始內部盤點及完整日誌先逐檔私人快照備份，公開保留方法與無詞統計。資料、模型、完整詞／Prompt／response、音訊及Session皆不列入新提交。

既有公開歷史有舊上游home參照與授權benchmark歌詞／trace；沒有改寫或自行刪除歷史，不能宣稱整個歷史零歌詞。新候選的安全盤點、精確路徑清單、測試與兩筆commit方案見[RELEASE_PREPARATION.md](RELEASE_PREPARATION.md)。只準備，等待人工確認commit／push，不切Phase4C分支。
