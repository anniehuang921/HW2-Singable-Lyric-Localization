# Phase3–4B Git Release Preparation

2026-10-21（Asia/Taipei）。**本輪只準備；未stage／commit／push／切分支／stash／reset／clean，也未刪除既有成果。**

## A. Git基準

- branch：main。HEAD `ad565d86e531f64064ed4d93520fde109f5041e5`。
- origin指向使用者Fork `https://github.com/anniehuang921/HW2-Singable-Lyric-Localization.git`，fetch／push同址，沒有URL憑證。
- `git ls-remote origin refs/heads/main`確認GitHub main與HEAD／本機origin/main一致，無遠端新增提交。只查詢，沒有fetch或更新ref。
- 盤點開始：2406 tracked files，6 modified tracked、31 untracked files，0 staged。新增檔均可追溯Phase3至4B；沒有檢出無關改動或BLT核心變更。最終建議清單另含本輪公開配置／報告與最小修正：7個modified tracked、34個untracked files，共41檔，0 staged。
- 使用status／branch -vv／log -10／diff --stat／diff --check／ls-files／status --ignored及staged列表；全量檔案清單與掃描結果只留本機，不在報告貼大量路徑或私人內容。

## B. 安全與既有歷史

### 新提交候選

所有tracked與非ignored untracked檔案做模式掃描；Phase3–4B程式／tests／scripts／docs另外核對來源與資料角色。沒有發現真實Key、Token、Authorization值、完整私人譯文、原始Codex Session、模型或音訊被列入候選。

測試中的合成憑證／句子是原創fixture，不是可用Key或真實翻譯。公開程式只保留讀取／核對邏輯，不內嵌官方曲目歌詞。

本輪最小修正：

- excerpt.py原有14個官方音素常值改為執行時從同stem官方txt讀取，再與CSV／MIDI核對；既有audit、音訊與結果不變。
- README改為HW2入口，保留上游原文件；增加架構、隔離環境、CSD取得、Key安全輸入、7864啟動／回播與限制。
- 補公開placeholder manifest，實際manifest仍ignored；保留固定權重來源／版本與已量測統計。
- 公開文件省略主機磁碟拓樸、共享目錄權限、其他研究環境占用等內部資訊。37份整理前候選原檔先逐檔備份、SHA驗證，完整原日誌及調查留ignored私人快照；沒有刪除私人紀錄。
- .gitignore擴充datasets／weights／checkpoints／環境／cache／log／Session／音訊／權重副檔名與credentials。`git ls-files -ci --exclude-standard`為0：沒有用忽略規則掩蓋已tracked檔案。

### 已存在公開歷史（本輪不改寫）

掃描main可達4318個歷史blob，未發現獨立憑證格式命中。單純舊regex曾誤中普通字串內部的`sk-`，以及lock中套件版本／wheel字樣，經上下文與邊界核對排除，未印出疑似值。

**需單獨知悉：** 歷史 `paper/phase_ablation_results.md`有home目錄參照，來自既有上游提交（相關歷史 `1f18b08`／`63224f9`）。沒有把路徑值帶到新報告，也沒有改寫歷史。歷史掃描不是完整專業秘密偵測的保證。

既有上游 `data/bench/`已含授權歌詞節錄與agent benchmark traces，屬先前公開歷史，授權見其README；與HW2私人CSD／Gemini／Codex資料不同，本輪不新增／刪除／改寫。**若公開政策要求整個Repository連歷史都不含任何歌詞或內部路徑，需另行決策；本輪不宣稱已達此條件。**

### 必須保留但不得提交

artifacts全部（CSD ZIP／WAV／MID／CSV／lyrics／phoneme／metadata、模型manifest、原始Prompt／response、譯文、生成音訊／stem／私人快照）、.venv-ui及其他本機環境、ignored舊實驗文件／catalog、API Key與原始Session／備份。Git忽略不代替本機權限或Git history審查，不能force-add。

## C. 明確提交清單與分組

權威檔案清單見 [RELEASE_FILES.json](RELEASE_FILES.json)，每個實際路徑都明列，不使用git add .或整個docs／artifacts目錄。包含本輪整理後的公開內容，排除所有ignored成果。

按功能階段分類（這是閱讀索引，實際stage仍以JSON逐檔清單為準）：

| 階段 | 候選範圍 |
|---|---|
| Phase3 | hw2_singing三個模組、start_singing_ui.sh、test_singing.py／phase3_live.py、docs/phase3公開文件／GPU依賴／manifest範例 |
| Phase4A | hw2_datasets的init／csd／presenter／verify_csd、extract_csd.py、test_csd.py／phase4a_live.py、docs/phase4a |
| Phase4B | hw2_datasets的excerpt／workflow、credential_check.py、run_csd_first_singing.py／start_csd_phase4b.sh、test_csd_excerpt.py／test_csd_credentials.py／phase4b_live.py、docs/phase4b |
| 共用／發布 | hw2_ui/app.py、.gitignore、README、Context／Decisions／CODEX_LOG／PUBLIC_RELEASE_REVIEW與本計畫／清單 |

建議兩個commits：

1. `feat: integrate YingMusic singing and CSD comparison workflows`：完整hw2_singing／hw2_datasets、新credential_check、共用hw2_ui/app.py、必要啟動／解壓／單曲runner、對應單元與可選live測試、.gitignore、GPU requirements與placeholder manifest。
2. `docs: document verified Phase 3–4B workflows and release review`：README、公開Context／Decisions／協作摘要、Phase3／4A／4B說明與無詞結果、公開審查及本計畫／清單。

跨階段app.py同時接Adapter、dataset與workflow，singing request也核對CSD excerpt。將其拆成三個階段會需要人工重建中間版本及測試fixture，增加漏依賴／選錯hunk風險；本計畫把完整功能鏈及測試放同一筆，文件第二筆，保留可運作與可追蹤的節點。若要更細分需另行授權實際準備／驗證中間樹，本輪未嘗試切分index或改寫檔案歷史。

以下**只是建議，不執行**。人工確認後可依JSON列出的每組精確路徑使用 `git add -- path1 path2 ...`；stage後必須重新檢查 `git diff --cached --name-status`、`git diff --cached --stat`、`git diff --cached --check`及安全掃描，確認沒有額外staged內容，再依組訊息commit。不要透過force-add私人檔案，不用reset／stash來拆分。

產生建議指令（只列印，不stage／commit）：

```bash
python3 - <<'PYPLAN'
import json, shlex
from pathlib import Path
for group in json.loads(Path('docs/RELEASE_FILES.json').read_text())['groups']:
    print(shlex.join(['git', 'add', '--', *group['files']]))
    print('git diff --cached --name-status')
    print('git diff --cached --stat')
    print('git diff --cached --check')
    print('# 完成安全審查、確認人工授權後才執行下一行')
    print(shlex.join(['git', 'commit', '-m', group['message']]))
PYPLAN
```

## D. 驗證

- 完整本機unittest：73通過，35.890秒。
- 只複製tracked＋非ignored候選到/tmp，沒有.git／環境／私人artifacts：73項執行，**63通過、10個官方素材條件測試skip**，35.942秒。不是宣稱公開副本有正式實驗或模型。
- Python AST語法74檔、Shell bash -n 4檔通過；git diff --check通過。
- CSD重新全量verify：50英＋50韓／200錄音通過，原1000檔SHA與舊驗證完全一致；兩份metadata與原ZIP內容相符，官方ZIP MD5不變。新驗證另存ignored私人位置，未覆寫原證據。
- 7865可選live：saved_csd_results=true、全文／片段／兩版音訊與EN_01回播通過，結束關閉自身服務。沒有新API／GPU。
- 實際7864：CSD英文兩版載入／下載SHA一致，韓文錄音、舊EN_01原比較及演唱回播正常，7863 HTTP200。未重啟既有服務，不讀舊程序Key。
- BLT src／skills／pyproject／uv.lock相對HEAD無diff，YingMusic git乾淨。未安裝、下載模型、重新翻譯或合成。

## E. 後續確認與分支

新候選內容已具備明確清單，可在人工確認安全範圍後stage／commit。Push本輪未授權，也未執行；需確認上述既有歷史範圍可接受、重新核對遠端main未變、逐筆staged審查與測試完成後才另行批准。

main應保存本輪Phase3–4B完整、可測且無私人產物的新節點。兩筆commit完成、工作目錄核對乾淨或僅預期ignored資料、遠端同步確認後，才建立 `feature/phase4c-full-song`；本輪仍留main。

若GitHub main有新提交：先停止發布，不覆蓋；保留本地改動，待已確認的本地節點保存後fetch／檢查分歧，再由使用者決定整合方式，重新跑測試。不要在髒目錄直接pull／rebase，不reset或force push。

Phase4C應另行批准片段／全曲策略、API／GPU預算與人工品質評估；Phase4D再改善切換延遲與比較操作。本輪沒有開始後續開發。
