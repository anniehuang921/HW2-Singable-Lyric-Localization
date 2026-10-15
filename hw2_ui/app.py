"""Local Gradio material browser and bounded Phase 2B comparison UI."""
import argparse
import os
from pathlib import Path
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
os.environ.setdefault('GRADIO_TEMP_DIR', '/tmp/hw2-gradio-cache')
import gradio as gr
from .catalog import DEFAULT_ROOT, read_catalog
from .presenter import AUDIO_CACHE, Presenter


def build_ui(presenter, controller=None, saved_only=False):
    from hw2_translation.controller import Controller
    controller = controller or Controller(presenter)
    choices = presenter.choices()
    initial = choices[0][1] if choices else None
    values = presenter.select(initial)
    with gr.Blocks(title='HW2 · 官方 Demo 素材瀏覽', analytics_enabled=False) as app:
        gr.Markdown('# HW2 · YingMusic 官方 Demo\n選擇素材，查看原詞並播放原始音訊。Phase 2B：翻譯比較與人工修訂。')
        with gr.Row():
            language = gr.Dropdown(['en', 'zh', '全部'], value='en', label='語言')
            task = gr.Dropdown(['全部', 'Lyric Editing', 'Melody Control'], value='全部', label='任務')
        selected = gr.Dropdown(choices, value=initial, filterable=True, label='官方 Demo（可輸入搜尋）')
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
        gr.Markdown('## YingMusic 中文演唱與音訊比較\n**尚未實作** · 本階段沒有生成中文演唱。')
        translation_outputs = [status,direct,assisted,direct_metrics,assisted_metrics,comparison_state,comparison_file,editor,edit_metrics,edit_file,editor_before]
        def run_translation(demo_id, progress=gr.Progress()):
            yield ['正在準備翻譯…','','',None,None,None,None,'',None,None,None]
            try:
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
        def load_saved_comparison(demo_id):
            try:
                record=controller.load_saved(demo_id)
                modes=record['modes']
                def details(mode):return {'demo_id':record['demo_id'],'segment_ids':record['segment_ids'],'source':record['source'],**modes[mode],'is_mock':False}
                return ['已載入真實比較 · '+demo_id+' · '+record['provider']['model']+'（沒有新 API 請求）',
                        '\n'.join(modes['direct']['segments']),'\n'.join(modes['blt_assisted']['segments']),
                        details('direct'),details('blt_assisted'),record,record['artifact_path'],'',None,None,None]
            except ValueError as exc:raise gr.Error(str(exc))
        load_saved_button.click(load_saved_comparison,selected,translation_outputs,api_name='load_saved_translation')
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
    return app


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--yingmusic-root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--port', type=int, default=7860)
    ap.add_argument('--saved-only', action='store_true'); args = ap.parse_args()
    presenter = Presenter(read_catalog(root=args.yingmusic_root), {'yingmusic_official': args.yingmusic_root})
    if args.saved_only:
        from hw2_translation.controller import Controller
        def disabled_provider():raise RuntimeError('結果檢閱模式不允許模型請求')
        app=build_ui(presenter,Controller(presenter,provider_factory=disabled_provider),saved_only=True)
    else:
        app = build_ui(presenter)
    app.launch(server_name='127.0.0.1', server_port=args.port, share=False,
               allowed_paths=[str(AUDIO_CACHE), str(Path(__file__).resolve().parents[1]/'artifacts'/'translations')], show_error=True, inbrowser=False)

if __name__ == '__main__':
    main()
