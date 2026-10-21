# Phase4B 兩次 Direct 失敗：離線診斷

2026-10-21（Asia/Taipei）。只讀取既有私人 experiment／comparison；沒有重新呼叫 Gemini 或 GPU、沒有讀取其他程序憑證。

| 執行 | comparison建立時間（UTC） | 實際請求 | HTTP | Google錯誤 | 後續 |
|---|---|---:|---:|---|---|
| 第一次 | 2026-10-20 22:30:15 | 1 | 400 | INVALID_ARGUMENT／code400／Please pass a valid API key | Direct失敗即停 |
| 第二次 | 2026-10-20 22:30:58 | 1 | 400 | 同上 | Direct失敗即停 |

兩次都使用OpenAI-compatible Provider，`gemini-3.5-flash-lite`，base URL `https://generativelanguage.googleapis.com/v1beta/openai/`，拼接後路徑 `/v1beta/openai/chat/completions`。temperature0.2、max_tokens4096、reasoning_effort low、timeout45秒，is_mock=false。總計2次API請求，沒有assisted、修訂或GPU請求，錯誤回應未提供token用量（不能寫成0 tokens）。

證據：私人receipt的request_count_this_execution皆1；各comparison只有direct的一筆attempt，api_response.http_status=400，errors保留Google安全錯誤。沒有raw_output、parsed segments或validation。comparison與experiment均成功寫入。因此根本失敗點是Google拒絕API Key，並非HTTP200後JSON解析、BLT、保存或模型503／404。

不能由此證明「Key完全沒傳入」或「使用者輸入的一定非空但無效」：舊紀錄刻意不留Key，沒有接收boolean，無法事後還原實際輸入。靜態檢查顯示原script已有read後export；本輪以原script實際read/export區塊和合成憑證做子程序測試，Python接收完全相同值且未輸出值。故沒有證據支持shell固定漏export；更不能從其他程序取Key來猜測。

最小修復：

- 新增離線credential_check，拒絕空值、空白／換行與外層引號；只回傳接收與輸入檢查boolean，不記值／長度／hash。通過不代表Google認證有效。
- Terminal隱藏輸入及export後先在Python檢查；runner同樣檢查，並把同一個已檢查Provider實例傳給Controller。
- 私人receipt保存接收boolean及底層errors；runner錯誤提示安全顯示Google錯誤，避免只報Translation failed。保留既有過濾、請求上限、錯誤即停與原始失敗紀錄。
- 3個合成測試通過：空值／引號／空白拒絕、安全boolean、原shell區塊→Python環境傳遞。bash -n／py_compile／git diff --check通過。

目前沒有更換模型、endpoint或生成參數的理由。下一步請使用者確認Tech HW2的API Key仍有效，重新從該專案複製Key字串本身，在原Terminal安全腳本隱藏輸入。程式可受控重跑，但**Key的Google有效性尚未確認，不能保證認證成功**。本輪未重跑整個Phase4B，也未要求把Key貼進對話。
