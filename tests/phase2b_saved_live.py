"""Replay true saved outputs and edit via same UI; provider is forbidden."""
import json
from pathlib import Path
from gradio_client import Client
from hw2_translation.controller import Controller
from hw2_translation.storage import DEFAULT_DIR
from hw2_ui.app import build_ui
from hw2_ui.catalog import read_catalog,DEFAULT_ROOT
from hw2_ui.presenter import Presenter

def main():
    def forbidden():raise RuntimeError('No LLM calls permitted in replay test')
    presenter=Presenter(read_catalog(),{'yingmusic_official':DEFAULT_ROOT})
    app=build_ui(presenter,Controller(presenter,provider_factory=forbidden),saved_only=True)
    results=[]
    try:
        app.launch(server_name='127.0.0.1',server_port=7864,share=False,prevent_thread_lock=True,quiet=True,allowed_paths=[str(DEFAULT_DIR.resolve())])
        client=Client('http://127.0.0.1:7864',verbose=False,download_files=False,analytics_enabled=False)
        for name in ['SingEdit_EN_01','SingEdit_EN_02']:
            client.predict(name,api_name='/select_demo')
            loaded=client.predict(name,api_name='/load_saved_translation')
            assert loaded[1] and loaded[2] and loaded[3]['is_mock'] is False
            candidate=client.predict(name,'blt_assisted',api_name='/load_candidate')
            edit=client.predict(name,'blt_assisted',candidate,api_name='/validate_edit')
            assert edit[0]['validation']['syllables_match'] is True
            results.append({'demo_id':name,'real_saved_outputs_loaded':True,'candidate_edit_validation':'PASS'})
        try:client.predict('SingEdit_EN_02',api_name='/translate')
        except Exception:pass
        # The normal handler catches RuntimeError/AssertionError; no provider ever returns content.
    finally:app.close()
    Path('docs/phase2b/gemini/real35lite/saved-ui-results.json').write_text(json.dumps({'new_llm_calls':0,'results':results},ensure_ascii=False,indent=2)+'\n')
    print('Saved real comparison UI replay: PASS; no LLM calls')

if __name__=='__main__':main()
