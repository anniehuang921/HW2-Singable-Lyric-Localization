# HW2 — Singable Lyric Localization

BLT Fork 上的 EN→ZH 歌詞翻譯與中文翻唱實驗系統。比較同模型 Direct LLM 與 BLT-assisted 翻譯，保留人工編輯與原版音節／押韻驗證，再以唯讀 YingMusic-Singer-Plus 推論。軟體不附官方音訊、完整歌詞、譯文、私人實驗、API Key 或模型權重。

## 已完成與架構

- Phase1：原版BLT Baseline；Phase2A／2B：官方Demo、Gemini兩版比較與人工編輯。
- Phase3：獨立GPU Worker、真實中文演唱、版本／輸入／輸出hash核對與保存結果回播。
- Phase4A：官方CSD 50英文＋50韓文、200份調性錄音的本機匯入／驗證／瀏覽。
- Phase4B：僅核對後的CSD_en042a兩句片段，兩版真實翻譯／演唱及操作播放驗收完成。73項回歸通過。
- Phase4C整曲與Phase4D操作優化尚未開始；韓文僅瀏覽，翻譯／演唱相容性未驗證。

```text
唯讀YingMusic presets / 本機CSD
            ↓ hw2_ui + hw2_datasets（song / recording / verified excerpt）
       hw2_translation → 同一Gemini → 原BLT subprocess工具
            ↓ 保存比較 / 人工編輯與驗證
       hw2_singing → 獨立離線GPU Worker → 本機WAV / hash核對回播
```

## 安裝前置條件

保留原版src／skills／pyproject.toml／uv.lock；需要Python3.11、uv及espeak（依作業系統自行安裝）。UI與GPU分開環境；不要將GPU依賴裝進BLT或UI環境。

```bash
# BLT：沿原鎖檔；不要覆寫已存在的環境
uv sync --locked --no-dev --python 3.11
export HW2_BLT_PYTHON="$PWD/.venv/bin/python"
# UI：獨立環境（若已存在則沿用）
uv venv --python 3.11 .venv-ui
uv pip install --python .venv-ui/bin/python -r docs/phase2b/ui-requirements.txt
```

YingMusic需另行依法取得官方Repo與模型，預設為此Repo的sibling `YingMusic-Singer-Plus`，或設定 `HW2_YINGMUSIC_ROOT`。模型／資料不會自動下載。實測GPU環境Python3.10／torch2.7.1-cu128／torchaudio2.7.1／torchvision0.22.1，完整說明、權重清單與manifest範例見[Phase3](docs/phase3/README.md)。GPU環境與模型有顯著磁碟需求，部署前自行確認相容性、授權與資源。

## 取得CSD

來源：[官方GitHub](https://github.com/equal-singer/CSD)、[固定Zenodo記錄](https://zenodo.org/records/4785016)。CC BY-NC-SA4.0，保留來源／引用與非商業／同方式分享限制，另遵守官方README聲音使用條件。資料放本機ignored artifacts；歌曲與a／b錄音分開計數。

先確認ZIP約1.85GB＋解壓約3.08GB及額外安全餘量，再手動下載；以下命令會消耗下載空間，**不要對既有ZIP重新執行下載**：

```bash
mkdir -p artifacts/datasets/csd
# 僅在CSD.zip尚不存在時下載；不需要API Key
test ! -e artifacts/datasets/csd/CSD.zip && curl --fail --location --output artifacts/datasets/csd/CSD.zip https://zenodo.org/api/records/4785016/files/CSD.zip/content
python3 scripts/extract_csd.py artifacts/datasets/csd/CSD.zip
.venv-ui/bin/python -m hw2_datasets.verify_csd --output artifacts/datasets/csd/verification.json
```

解壓工具先驗官方MD5／CRC／路徑及10GiB本機保留量，目的資料已存在時拒絕覆寫。保留WAV、MIDI、CSV、歌詞／phoneme及metadata。可用 `HW2_CSD_ROOT` 指定其他完整本機資料根目錄。詳[Phase4A](docs/phase4a/README.md)。

## 啟動7864與安全Key

已有模型manifest／既有成果時，無Key檢閱：

```bash
# 實際manifest只放ignored artifacts，不能提交；範例不能直接當真實配置
export HW2_SINGING_PYTHON="$HOME/.conda/envs/hw2-yingmusic/bin/python"
export HW2_SINGING_MANIFEST="$PWD/artifacts/deployment/singing-manifest.json"
# 已有核對片段時啟用其回播
export HW2_CSD_PHASE4B=1
bash scripts/start_singing_ui.sh
```

初次取得CSD片段（已安裝完整資料時）：`.venv-ui/bin/python -m hw2_datasets.excerpt`。將核對／人工聽辨視為實驗前置，不能只根據音節數假設音訊對齊。

需要首次真實CSD翻譯與兩版生成時，使用 `bash scripts/start_csd_phase4b.sh`。此操作**會發API請求及使用GPU**，須有可用Key、模型與資源授權：

- 在Terminal隱藏輸入Key，只貼Key字串，不貼進對話、argv、程式碼或檔案。
- 固定已驗證Gemini設定；本輪僅單首已核對片段、最多4請求、assisted最多2次修訂，API錯誤即停止、不自動重試／切模型。
- 成功後啟動相同7864；已保存正式候選優先讀快取，不重新生成。

服務只監聽127.0.0.1、share=False；VS Code Remote SSH的Ports轉發7864，在瀏覽器開啟轉發網址。若端口已使用，確認是自己的本案服務後先在其Terminal停止，勿中斷其他服務。

操作：CSD → English → Twinkle… → a → 看完整原曲與核對兩句片段 → 開始翻譯或載入真實比較 → 選Direct／assisted → 生成或載入已生成演唱 → 三音軌比較。保存結果只留 `artifacts/translations/`、`artifacts/singing/`，尚未生成不顯示假音訊。其他CSD／韓文仍只瀏覽；完整歌詞／原聲／衍生歌曲不公開提交。

## 測試、結果與限制

```bash
PYTHONPATH=.:tests .venv-ui/bin/python -m unittest discover -s tests -v
# 可選整合：需本機官方資料／私人正式結果；暫用7865，結束關閉；不發API／GPU
PYTHONPATH=.:tests .venv-ui/bin/python tests/phase4b_live.py
```

[Phase4B結果](docs/phase4b/RESULTS.md)只公開統計：成功本輪3請求／1283tokens，兩版真實WAV約11.05秒；assisted修訂改善押韻但pattern下降。操作驗收與機器符合不等於語義、自然度或可唱性優劣通過。完整私人結果不隨Git提供，乾淨clone不能直接重播別人的實驗。

原版標點押韻及validator feedback限制保留；BLT-assisted是依Skill規則的移植編排，不是完整原Agent重現。較長片段／整曲／自動分段拼接與介面效能仍待後續驗證。

[發布盤點與提交計畫](docs/RELEASE_PREPARATION.md) · [公開／私人分界](docs/PUBLIC_RELEASE_REVIEW.md) · [Baseline](docs/baseline/BASELINE_REPORT.md)

---

## Original BLT documentation (upstream)

以下保留上游工具與benchmark說明；其可選Claude／Modal流程不屬於HW2本機測試，也不會由UI自行啟用。

# blt-skills

Agent Skills for lyrics translation, following the [Agent Skills spec](https://agentskills.io/specification).

Translate lyrics between languages while preserving syllable counts, rhyme scheme, and word-level syllable patterns.

## Skills

| Skill | Description |
|-------|-------------|
| [lyrics-translator](skills/lyrics-translator/SKILL.md) | Orchestrates the full translation pipeline |
| [syllable-counter](skills/syllable-counter/SKILL.md) | Count syllables in text |
| [rhyme-analyzer](skills/rhyme-analyzer/SKILL.md) | Detect rhyme endings and schemes |
| [syllable-pattern-analyzer](skills/syllable-pattern-analyzer/SKILL.md) | Analyze word-level syllable distribution |
| [phonetic-analyzer](skills/phonetic-analyzer/SKILL.md) | IPA conversion and phonetic similarity |
| [lyrics-validator](skills/lyrics-validator/SKILL.md) | Verify translation constraints |

## Setup

Requires Python 3.11+ and espeak (for phonemizer).

```bash
# Install espeak
brew install espeak-ng

# Install pkg
uv sync --all-extras
```

## Data

English lyrics from [brunokreiner/genius-lyrics](https://huggingface.co/datasets/brunokreiner/genius-lyrics) (~481K songs from Genius, with artist/title/language metadata). Stored in `data/`.

```bash
# Download
uvx --from huggingface_hub hf download brunokreiner/genius-lyrics --repo-type dataset --local-dir data/genius-lyrics
```

The sampled Ou et al. (2023) evaluation windows and associated generated benchmark artifacts under `data/bench/` are distributed under the source dataset's [CC BY-NC-SA 4.0 license](https://huggingface.co/datasets/LongshenOu/lyric-trans-en2zh-data). They are not covered by the repository's Apache-2.0 software license; see `data/bench/README.md`.

## Benchmark

Expose the skills to Claude Code, then run the agent benchmark on the Ou et al. (2023) en-zh test windows (`-n`, `--seed`, `--target-lang`, `-o`):

```bash
ln -s ../skills .claude/skills
uv run scripts/run_agent.py -n 100 --model claude-haiku-4-5-20251001 --workers 4
uv run scripts/run_agent.py -n 30 --model claude-haiku-4-5-20251001 --target-lang ja
uv run scripts/run_agent.py -n 100 --model claude-haiku-4-5-20251001 --skill none   # tool-free single-prompt baseline
uv run scripts/run_agent.py -n 100 --model claude-haiku-4-5-20251001 --skill lyrics-translator-prompt-only --disallowed-tools Bash,Agent,Task
```

Each item is one `claude -p` call that receives only the source lines (pass exact model IDs; aliases such as `opus` move between model versions); the trace of every tool call is saved under `data/bench/<run>/traces/`, and `--skill none` denies every tool for the baseline. Evaluate and score with:

```bash
uv run scripts/eval_fixed.py --songs <run>/test_songs.json --out data/bench/final.json vanilla=<vanilla_run>/partial agent=<run>/partial
uv run scripts/build_comet_payload.py --out /tmp/comet.json blt=<run>/partial vanilla=<vanilla_run>/partial
modal run scripts/modal_comet.py --payload /tmp/comet.json --out data/bench/semantic_scores.json
```

The CLT baseline (`data/bench/clt_translations.json`) comes from `scripts/clt_infer_original.py`, run inside a checkout of [ControllableLyricTranslation](https://github.com/Sonata165/ControllableLyricTranslation) with our syllable targets (`data/bench/clt_lengths_fixed.json`).

## Dependencies

- `phonemizer` - IPA conversion via espeak
- `pypinyin` - Chinese pinyin extraction
- `panphon` - IPA phonetic similarity
- `jieba` - Chinese word segmentation
- `pydantic` - data models
- `torch`, `transformers`, `sentencepiece` - CLT baseline only (optional, `uv sync --extra clt`)
- `ruff` - linting and formatting (optional, `uv sync --extra dev`)

## License

The software and original documentation are licensed under Apache-2.0. Third-party lyric excerpts and derived benchmark artifacts under `data/bench/` retain the dataset license described above.
