# Phase 4B 最終結果：操作驗收通過

2026-10-21（Asia/Taipei）。使用者明確確認7864已顯示兩版中文歌詞，Direct／BLT-assisted演唱均可播放。此為操作與播放驗收，不等於語義、自然度或可唱性優劣已評分。本輪只核對既有成果，0次新翻譯／0次新合成。

## 來源與公平條件

- CSD_en042a，Twinkle Twinkle Little Star，前兩行；來源片段2.60–13.65秒，11.05秒，目標音節[7,7]／原韻式AA。
- 官方同stem歌詞、14個音素、MIDI音高與CSV時間及波形已核對，最大MIDI／CSV時間差0.000048秒；最終發音邊界品質仍可人工聽辨。
- 兩版request逐欄核對：相同原文、source segments、reference text、original／melody／timbre audio、input SHA與設定。
- 固定官方Plus revision9b3f444f2bccd77fbc03e32eb7c334fc96040b8d；seed666、NFE32、CFG3、t_shift0.5、sil_len_to_end0.5，純人聲不分離／不混音。繁體原文保留，送入模型副本t2s。
- 完整英文、兩版中文、Prompt、raw response及音訊留本機ignored artifacts，公開報告不重散布。完整私人整理見 `artifacts/phase4b/FINAL_RESULTS.md`。

## 翻譯與限制比較

| 指標 | Direct | BLT-assisted最終 |
|---|---|---|
| 音節 | 7、10 | 7、7 |
| 精確符合音節行數 | 1/2 | 2/2 |
| 韻尾 | ing／e | ing／ing |
| 原版rhymes_valid | false | true |
| 字詞pattern精確符合 | false | false |
| pattern similarity | 0.736607 | 0.733631 |
| 有限修訂次數 | 0 | 1 |
| 流程最終狀態 | completed | completed |

Assisted初版為7／7、韻尾ing／ui、押韻不通過、pattern similarity0.897321；一次修訂後維持7／7、改為ing／ing通過，pattern similarity下降至0.733631。修訂改善押韻，並非所有指標改善。引擎completed表示音節／押韻／段數／漢字限制符合，沒有要求pattern精確符合；完整validator feedback仍保留。Direct原輸出沒有為分數事後縮短，10音節第二行也真實完成合成。

## 真實Gemini使用量

同一OpenAI-compatible Provider／gemini-3.5-flash-lite，temperature0.2／max_tokens4096／reasoning_effort low／timeout45秒，三次均HTTP200且response_model相符。

| 請求 | prompt tokens | completion tokens | total |
|---|---:|---:|---:|
| Direct | 127 | 89 | 216 |
| Assisted初版 | 248 | 64 | 312 |
| Assisted修訂1 | 689 | 66 | 755 |
| 成功本輪合計3請求 | 1064 | 219 | 1283 |

加上先前兩次HTTP400失敗，Phase4B已留存紀錄的總API請求為5次。400回應沒有usage，所以1283是成功本輪已知tokens，不能宣稱是含失敗請求的確定總量。Free Tier設定沿用，未啟用Billing。早期失敗紀錄完整保留。

## 真實YingMusic音訊

兩份私有WAV均有對應request／result／metrics／worker.log與SYNTHESIS_SUCCESS，is_mock=false、model ID／revision匹配。重新全長解碼驗證44.1kHz／雙聲道／487424frames／有限值／非靜音。兩份WAV各11.052698秒，比來源多約2.70ms；兩版與來源SHA均不同，輸出SHA與保存／HTTP下載一致。

| 指標 | Direct | Assisted |
|---|---:|---:|
| Controller整體耗時（含子程序） | 17.985秒 | 23.192秒 |
| Worker整體耗時 | 16.477秒 | 21.682秒 |
| 模型載入 | 9.284秒 | 14.388秒 |
| 聲學生成 | 1.386秒 | 1.397秒 |
| CUDA peak allocated | 4.285GiB | 4.285GiB |
| CUDA peak reserved | 5.748GiB | 5.748GiB |
| 解碼RMS | 0.129123 | 0.121283 |
| peak amplitude | 0.512996 | 0.451883 |

硬體RTX5090，PyTorch2.7.1+cu128。VRAM是torch allocator峰值，非NVML整卡峰值；不同載入耗時不代表哪種歌詞較好。私人精確WAV路徑及SHA見本機FINAL_RESULTS。

## 回播與回歸

- 7864實際呼叫load_saved_translation／load_saved_singing：兩版各重載2次、HTTP200、WAV SHA與正式檔案一致；只載入，未呼叫translate／generate_singing。
- 已核對英文片段、韓文kr001原音、舊EN_01 comparison與中文演唱、7863均HTTP200。韓文仍只瀏覽，不宣稱翻譯／演唱相容。
- `tests/phase4b_live.py`：7865暫服，saved_csd_results=true，兩版正式結果回播、全文／片段、舊EN_01通過，0API／0GPU；測後關閉。
- `PYTHONPATH=.:tests .venv-ui/bin/python -m unittest discover -s tests -v`：73項通過35.989秒，包含原版BLT工具及各階段回歸。不另重跑Phase1全部CLI，也不將mock單元測試當新真實推論。
- 實際7864測試起初未選韓文歌曲便直接送另一錄音ID，Gradio正確拒絕；修正測試操作順序後通過，未修改程式或放寬驗證。
- git diff --check通過，原版BLT／lock／pyproject未修改，YingMusic乾淨。沒有commit／push；既有未提交工作保留。

操作：轉發7864 → CSD／English／Twinkle／a → 載入已保存真實比較 → 選Direct或BLT-assisted → 載入已生成演唱。片段播放器與兩版中文播放器可直接比較，不需重新輸入Key、發API或GPU作業（現有服務仍在運行）。

## Phase 4C 建議（尚未開始）

1. 先擴充同曲較長且完整樂句的短段，逐級量測耗時、顯存、對齊與失敗率，再決定單段長度；目前只驗證11.05秒。原模型sample使用準備後total_len，沒有本輪整曲容量證據。
2. 建立歌曲→段落→歌詞行→音符／CSV時間的固定映射與可稽核manifest；保留副歌／重複句ID與全曲上下文，兩方法使用相同分段及模型設定。
3. 全曲優先評估分段生成、快取與斷點續行，再按原始時間軸拼接；利用句間空白處理接縫，保護首尾發音與原始停頓，不任意壓縮Direct。
4. 小規模試跑前設定單曲API／修訂／GPU預算及停止條件；收集語義、自然度、節奏與發音的人工作業表，分開報告工具符合與聽感。
5. Phase4D再集中改善來源切換延遲、進度／錯誤提示及一鍵載入三音軌，沿用現有UI與Adapter。以上為建議，沒有部署、生成或隱含下一階段授權。

Phase4B收尾完成；停待後續人工決定，不自動開始Phase4C／4D。
