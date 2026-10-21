"""Local Gradio material browser and bounded Phase 2B comparison UI."""
import argparse
import os
from pathlib import Path
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
os.environ.setdefault('GRADIO_TEMP_DIR', '/tmp/hw2-gradio-cache')
import gradio as gr
from .catalog import DEFAULT_ROOT, read_catalog
from .presenter import AUDIO_CACHE, Presenter


def build_ui(presenter, controller=None, saved_only=False, singing=False, singing_controller=None):
    from hw2_translation.controller import Controller
    controller = controller or Controller(presenter)
    choices = presenter.choices()
    initial = choices[0][1] if choices else None
    values = presenter.select(initial)
    with gr.Blocks(title='HW2 · 官方 Demo 素材瀏覽', analytics_enabled=False) as app:
        gr.Markdown('# HW2 · 歌曲素材瀏覽\n選擇素材，查看原詞並播放原始音訊。Phase 2B：翻譯比較與人工修訂。')
        csd = getattr(presenter, 'csd', None)
        source = gr.Dropdown([('YingMusic Official Demo','yingmusic_official'),('CSD','csd')], value='yingmusic_official', label='資料來源', interactive=csd is not None)
        if csd is None:gr.Markdown(getattr(presenter,'csd_issue','CSD 尚未安裝；可設定 HW2_CSD_ROOT 至完整官方資料目錄後重新啟動。'))
        with gr.Row() as official_filters:
            language = gr.Dropdown(['en', 'zh', '全部'], value='en', label='語言')
            task = gr.Dropdown(['全部', 'Lyric Editing', 'Melody Control'], value='全部', label='任務')
        with gr.Row(visible=False) as csd_filters:
            csd_language = gr.Dropdown([('English','en'),('한국어','ko')],value='en',label='CSD 語言')
            csd_song = gr.Dropdown(csd.songs() if csd else [],label='CSD 歌曲（可搜尋）',filterable=True)
        gr.Markdown('CSD：[官方來源](https://zenodo.org/records/4785016) · [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。Choi et al., ISMIR 2020. 僅供非商業使用；保留姓名標示、同方式分享及官方聲音使用限制。CSD 僅已核對的 Phase 4B 英文片段可翻譯／合成；其他錄音僅瀏覽，韓文相容性待驗證。')
        selected = gr.Dropdown(choices, value=initial, filterable=True, label='官方 Demo／CSD 調性錄音（可輸入搜尋）')
        summary = gr.Markdown(values[0])
        with gr.Row():
            lyrics = gr.Textbox(values[1], label='原始歌詞（保留片段邊界）', lines=7, interactive=False)
            with gr.Column():
                original = gr.Audio(values[2], label='原始演唱音訊', interactive=False, type='filepath')
                melody = gr.Audio(values[3], label='旋律音訊（與 Timbre Reference 不同時）', interactive=False, visible=values[3] is not None)
        with gr.Accordion('Timbre Reference 與素材來源', open=False):
            timbre = gr.Audio(values[4], label='Timbre Reference Audio', interactive=False)
            reference = gr.Textbox(values[5], label='Reference Text（屬 timbre 音訊）', lines=4, interactive=False)
            metadata = gr.JSON(values[6], label='歌詞行數、音訊長度與官方來源')
        gr.Markdown('官方素材來源：[ASLP-lab/YingMusic-Singer-Plus](https://github.com/ASLP-lab/YingMusic-Singer-Plus)。音訊僅供學術研究與示範。')
        excerpt_text=gr.Textbox(label='已核對翻譯／演唱片段原詞（完整歌詞仍保留上方）',interactive=False,lines=3)
        excerpt_audio=gr.Audio(label='已核對英文片段 · 與兩份中文演唱使用相同來源',interactive=False)
        def get_excerpt(rid):
            audit=getattr(presenter,'excerpt',None)
            if not audit or audit['recording_id']!=rid:return '',None
            return '\n'.join(audit['segments']),audit['audio_path']
        selected.change(get_excerpt,selected,[excerpt_text,excerpt_audio],api_name='verified_excerpt')
        gr.Markdown('## EN→ZH 翻譯比較\n同一模型；Direct 不提供音樂限制，BLT-assisted 使用原版工具的有限修訂編排。')
        translate_button = gr.Button('開始翻譯', variant='primary', interactive=not saved_only)
        status = gr.Markdown('已保存結果檢閱模式：請載入真實比較，不發新 API 請求。' if saved_only else 'LLM 未配置時會顯示原因；mock 不出現在一般操作中。')
        comparison_state = gr.State(None)
        with gr.Row():
            with gr.Column():
                direct = gr.Textbox(label='Direct LLM · 繁體中文', lines=7, interactive=False)
                direct_metrics = gr.JSON(label='Direct · 英文原段與原版 BLT 音節／押韻驗證')
            with gr.Column():
                assisted = gr.Textbox(label='BLT-assisted · 繁體中文', lines=7, interactive=False)
                assisted_metrics = gr.JSON(label='BLT-assisted · 英文原段、驗證與修訂狀態')
        comparison_file = gr.File(label='翻譯實驗紀錄（Prompt、原始回應、設定與每次修訂）', interactive=False)
        load_saved_button = gr.Button('載入已保存的真實比較（不呼叫 API）')
        gr.Markdown('## 中文歌詞人工修改\n每個原片段對應一行；禁止變更段數。驗證符合不代表可唱性或語義品質已驗收。')
        candidate_mode = gr.Dropdown([('Direct LLM','direct'),('BLT-assisted','blt_assisted')], value='blt_assisted', label='候選版本')
        load_candidate = gr.Button('載入候選供編輯')
        editor = gr.Textbox(label='人工編輯中文歌詞', lines=7)
        editor_before = gr.State(None)
        validate_button = gr.Button('重新驗證並保存編輯')
        edit_metrics = gr.JSON(label='人工版本驗證與片段 ID')
        edit_file = gr.File(label='編輯前後版本紀錄', interactive=False)
        if singing:
            from hw2_singing.adapter import SingingController, configuration
            singer=singing_controller or SingingController(presenter)
            readiness=configuration()
            gr.Markdown('## YingMusic 中文演唱與音訊比較\n載入已有翻譯後選擇候選；不重新呼叫Gemini。原英文播放器位於上方。')
            singing_choice=gr.Dropdown([('BLT-assisted','blt_assisted'),('Direct LLM','direct'),('人工編輯版本','edited')],value='blt_assisted',label='演唱歌詞來源')
            gr.Markdown('固定比較設定：Seed 666、32 steps、CFG 3、t-shift 0.5。官方Demo分離／混音；已核對CSD純人聲片段不分離、不混音。僅推論副本轉簡體。')
            singing_button=gr.Button('生成中文演唱')
            saved_singing_button=gr.Button('載入已生成演唱（不重新推論）')
            singing_status=gr.Markdown('本機推論尚未就緒：'+'；'.join(readiness['issues']) if not readiness['ready'] else '本機已配置；請只測本階段核准的來源與候選。')
            singing_metrics=gr.JSON(label='演唱設定、實際送入文字、耗時與錯誤')
            with gr.Row():
                direct_audio=gr.Audio(label='Direct 中文演唱（未生成時為空）',interactive=False)
                assisted_audio=gr.Audio(label='BLT-assisted 中文演唱（未生成時為空）',interactive=False)
                edited_audio=gr.Audio(label='人工編輯中文演唱（未生成時為空）',interactive=False)
            singing_file=gr.File(label='本機演唱紀錄下載',interactive=False)
            singing_state=gr.State({})
            singing_outputs=[singing_status,singing_metrics,direct_audio,assisted_audio,edited_audio,singing_file,singing_state]
            def reset_singing():return ['請載入目前Demo的翻譯並選擇演唱候選。',None,None,None,None,None,{}]
            def generate_singing(demo_id,record,mode,text,before,cache):
                cache=dict(cache or {})
                if cache.get('_demo')!=demo_id:cache={'_demo':demo_id}
                yield ['正在處理演唱請求…',gr.skip(),gr.skip(),gr.skip(),gr.skip(),None,gr.skip()]
                try:
                    if demo_id in presenter.demos and presenter.demos[demo_id].source_type=='csd':raise ValueError('CSD Phase 4A 僅瀏覽；請等待 Phase 4B 片段核對與推論授權')
                    result=singer.generate(demo_id,record,mode,text,before)
                    cache[mode]=result.get('audio')
                    label=result['status']+' · '+str(result['elapsed_seconds'])+'秒'
                    if result.get('is_mock'):label+=' · MOCK，未生成音訊'
                    if result.get('error'):label+=' · '+result['error']
                    yield [label,result,cache.get('direct'),cache.get('blt_assisted'),cache.get('edited'),result['artifact_path'],cache]
                except (ValueError,RuntimeError) as exc:
                    cache.pop(mode,None)
                    yield [str(exc),{'status':'failed','error':str(exc)},cache.get('direct'),cache.get('blt_assisted'),cache.get('edited'),None,cache]
            singing_event=singing_button.click(generate_singing,[selected,comparison_state,singing_choice,editor,editor_before,singing_state],singing_outputs,api_name='generate_singing',concurrency_id='hw2-singing',concurrency_limit=1)
            def load_singing(demo_id,record,mode,text,before,cache):
                try:
                    result=singer.load_saved(demo_id,record,mode,text,before)
                    cache=dict(cache or {}) if (cache or {}).get('_demo')==demo_id else {'_demo':demo_id}
                    cache[mode]=result['audio']
                    return ['已載入真實演唱，沒有新GPU推論',result,cache.get('direct'),cache.get('blt_assisted'),cache.get('edited'),result['artifact_path'],cache]
                except (ValueError,RuntimeError) as exc:raise gr.Error(str(exc))
            saved_singing_button.click(load_singing,[selected,comparison_state,singing_choice,editor,editor_before,singing_state],singing_outputs,api_name='load_saved_singing')
            for component in (selected,language,task):component.change(reset_singing,None,singing_outputs,cancels=[singing_event],api_name=False)
        else:
            gr.Markdown('## YingMusic 中文演唱與音訊比較\nPhase 3 使用 --singing 開啟；未生成時不顯示合成音訊。')
        translation_outputs = [status,direct,assisted,direct_metrics,assisted_metrics,comparison_state,comparison_file,editor,edit_metrics,edit_file,editor_before]
        def run_translation(demo_id, progress=gr.Progress()):
            yield ['正在準備翻譯…','','',None,None,None,None,'',None,None,None]
            try:
                if demo_id in presenter.demos and presenter.demos[demo_id].source_type=='csd':raise ValueError('CSD Phase 4A 不呼叫翻譯；英文片段留待 Phase 4B，韓文相容性待驗證')
                record=controller.translate(demo_id,lambda text:progress(0.5,desc=text))
                modes=record['modes']
                def text(mode):return '\n'.join(modes.get(mode,{}).get('segments',[]))
                def details(mode):return {'demo_id':record['demo_id'],'segment_ids':record['segment_ids'],'source':record['source'],**modes.get(mode,{}),'is_mock':record['is_mock']}
                label='MOCK 測試資料，非真實翻譯' if record['is_mock'] else 'LLM 實際回應（品質待人工評估）'
                label+=' · '+record['demo_id']+' · '+', '.join(k+': '+v['status'] for k,v in modes.items())
                if record['errors']:label+=' · '+str(record['errors'])
                yield [label,text('direct'),text('blt_assisted'),details('direct'),details('blt_assisted'),record,record['artifact_path'],'',None,None,None]
            except (ValueError,RuntimeError) as exc:
                yield [str(exc),'','',None,None,None,None,'',None,None,None]
        event=translate_button.click(run_translation,selected,translation_outputs,api_name='translate',concurrency_limit=1)
        if singing:event.then(reset_singing,None,singing_outputs,api_name=False)
        def load_saved_comparison(demo_id):
            try:
                record=controller.load_saved(demo_id)
                modes=record['modes']
                def details(mode):return {'demo_id':record['demo_id'],'segment_ids':record['segment_ids'],'source':record['source'],**modes[mode],'is_mock':False}
                return ['已載入真實比較 · '+demo_id+' · '+record['provider']['model']+'（沒有新 API 請求）',
                        '\n'.join(modes['direct']['segments']),'\n'.join(modes['blt_assisted']['segments']),
                        details('direct'),details('blt_assisted'),record,record['artifact_path'],'',None,None,None]
            except ValueError as exc:raise gr.Error(str(exc))
        saved_event=load_saved_button.click(load_saved_comparison,selected,translation_outputs,api_name='load_saved_translation')
        if singing:saved_event.then(reset_singing,None,singing_outputs,api_name=False)
        def choose(demo_id,record,mode):
            try:
                lines=controller.candidate(demo_id,record,mode)
                return '\n'.join(lines),{'demo_id':demo_id,'mode':mode,'lines':lines}
            except ValueError as exc:raise gr.Error(str(exc))
        load_candidate.click(choose,[selected,comparison_state,candidate_mode],[editor,editor_before],api_name='load_candidate')
        def edit(demo_id,record,mode,text,before):
            try:
                if before is None:raise ValueError('請先載入候選供編輯')
                result,path=controller.edit(demo_id,record,mode,text,before)
                return result,path,{'demo_id':demo_id,'mode':mode,'lines':result['after']}
            except (ValueError,RuntimeError) as exc:raise gr.Error(str(exc))
        validate_button.click(edit,[selected,comparison_state,candidate_mode,editor,editor_before],[edit_metrics,edit_file,editor_before],api_name='validate_edit')
        def reset_translation():return ['Demo 已切換，請開始翻譯。','','',None,None,None,None,'',None,None,None]
        # Clear both translations and editing state when the source changes; cancel in-flight generator.
        selected.change(reset_translation,None,translation_outputs,cancels=[event],api_name=False)
        language.change(reset_translation,None,translation_outputs,cancels=[event],api_name=False)
        task.change(reset_translation,None,translation_outputs,cancels=[event],api_name=False)
        outputs = [summary, lyrics, original, melody, timbre, reference, metadata]
        def select(demo_id):
            result = list(presenter.select(demo_id))
            result[3] = gr.Audio(value=result[3], visible=result[3] is not None, interactive=False)
            return result
        def filter_demos(lang, kind):
            options = presenter.choices(lang, kind)
            value = options[0][1] if options else None
            return [gr.Dropdown(choices=options, value=value), *select(value)]
        selected.change(select, selected, outputs, api_name='select_demo')
        language.change(filter_demos, [language, task], [selected, *outputs], api_name='filter_language')
        task.change(filter_demos, [language, task], [selected, *outputs], api_name='filter_task')
        def csd_selection(lang,song):
            songs=csd.songs(lang) if csd else []
            valid={value for _,value in songs}
            song=song if song in valid else (songs[0][1] if songs else None)
            variants=csd.variants(song) if csd else []
            value=variants[0][1] if variants else None
            return [gr.Dropdown(choices=songs,value=song),gr.Dropdown(choices=variants,value=value),*select(value)]
        def change_source(kind,csd_lang,official_lang,official_task):
            if kind=='csd' and csd:
                return [gr.Row(visible=False),gr.Row(visible=True),*csd_selection(csd_lang,None),
                        gr.Button(interactive=False),*reset_translation()]
            options=presenter.choices(official_lang,official_task)
            value=options[0][1] if options else None
            return [gr.Row(visible=True),gr.Row(visible=False),gr.Dropdown(value=None),
                    gr.Dropdown(choices=options,value=value),*select(value),
                    gr.Button(interactive=not saved_only),*reset_translation()]
        source.change(change_source,[source,csd_language,language,task],[official_filters,csd_filters,csd_song,selected,*outputs,translate_button,*translation_outputs],cancels=[event],api_name='select_source')
        csd_language.change(csd_selection,[csd_language,csd_song],[csd_song,selected,*outputs],api_name='csd_language')
        csd_song.input(csd_selection,[csd_language,csd_song],[csd_song,selected,*outputs],api_name='csd_song')
        def eligibility(rid):
            enabled=presenter.demos.get(rid) is not None and presenter.demos[rid].source_type!='csd'
            return gr.Button(interactive=enabled and not saved_only)
        selected.change(eligibility,selected,translate_button,api_name=False)
        if singing:
            selected.change(lambda rid:gr.Button(interactive=rid in presenter.demos and presenter.demos[rid].source_type!='csd'),selected,singing_button,api_name=False)
            source.change(reset_singing,None,singing_outputs,cancels=[singing_event],api_name=False)
            source.change(lambda kind:gr.Button(interactive=kind!='csd'),source,singing_button,api_name=False)

    return app


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--yingmusic-root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--port', type=int, default=7860)
    ap.add_argument('--saved-only', action='store_true'); ap.add_argument('--singing',action='store_true'); args = ap.parse_args()
    presenter = Presenter(read_catalog(root=args.yingmusic_root), {'yingmusic_official': args.yingmusic_root})
    from hw2_datasets.csd import CSD, DEFAULT_ROOT as CSD_ROOT
    if CSD_ROOT.is_dir():
        from hw2_datasets.presenter import DatasetPresenter
        try:
            presenter=DatasetPresenter(list(presenter.demos.values()),presenter.source_roots,CSD(CSD_ROOT))
            if os.getenv('HW2_CSD_PHASE4B')=='1':
                from hw2_datasets.excerpt import load
                presenter.enable_excerpt(load())
        except (ValueError,OSError,RuntimeError,KeyError) as exc:
            presenter.csd_issue='CSD 資料未通過讀取檢查，已停用此來源；既有官方 Demo 保留。原因：'+str(exc)
    if args.saved_only:
        from hw2_translation.controller import Controller
        def disabled_provider():raise RuntimeError('結果檢閱模式不允許模型請求')
        app=build_ui(presenter,Controller(presenter,provider_factory=disabled_provider),saved_only=True,singing=args.singing)
    else:
        if os.getenv('HW2_CSD_PHASE4B')=='1':
            from hw2_datasets.workflow import ExcerptController,ExcerptSinger
            app=build_ui(presenter,ExcerptController(presenter),singing=args.singing,singing_controller=ExcerptSinger(presenter))
        else:app = build_ui(presenter,singing=args.singing)
    app.launch(server_name='127.0.0.1', server_port=args.port, share=False,
               allowed_paths=[str(AUDIO_CACHE), str(Path(__file__).resolve().parents[1]/'artifacts'/'translations'), str(Path(__file__).resolve().parents[1]/'artifacts'/'singing'),str(Path(__file__).resolve().parents[1]/'artifacts/datasets/csd/excerpts')], show_error=True, inbrowser=False)

if __name__ == '__main__':
    main()
