"""Temporary mock-only Gradio server; real BLT tools, no live LLM service."""
import json
import tempfile
from pathlib import Path
from gradio_client import Client
from hw2_ui.app import build_ui
from hw2_ui.catalog import read_catalog, DEFAULT_ROOT
from hw2_ui.presenter import Presenter
from hw2_translation.controller import Controller
from hw2_translation.providers import MockProvider

def main():
    demos=read_catalog();presenter=Presenter(demos,{'yingmusic_official':DEFAULT_ROOT})
    rows=[]
    artifacts=[]
    with tempfile.TemporaryDirectory() as directory:
        responses=[]
        # A single factory uses the currently requested source prompt's IDs.
        class DynamicMock(MockProvider):
            def generate(self,prompt):
                self.prompts.append(prompt)
                name='SingEdit_EN_02' if 'SingEdit_EN_02' in prompt else 'SingEdit_EN_01'
                count=4 if name.endswith('02') else 2
                return json.dumps({'segments':[{'id':f'{name}:{i+1:03d}','text':'測試歌詞'} for i in range(count)]},ensure_ascii=False)
        controller=Controller(presenter,lambda:DynamicMock([]),directory=Path(directory))
        app=build_ui(presenter,controller)
        try:
            app.launch(server_name='127.0.0.1',server_port=7862,share=False,prevent_thread_lock=True,quiet=True,allowed_paths=[directory])
            client=Client('http://127.0.0.1:7862',verbose=False,download_files=False,analytics_enabled=False)
            for name in ['SingEdit_EN_01','SingEdit_EN_02']:
                client.predict(name,api_name='/select_demo')
                result=client.predict(name,api_name='/translate')
                assert 'MOCK' in result[0] and result[1] and result[2]
                text=client.predict(name,'direct',api_name='/load_candidate')
                assert len(text.splitlines())==(2 if name.endswith('01') else 4)
                edited='\n'.join('人工歌詞' for _ in text.splitlines())
                saved=client.predict(name,'direct',edited,api_name='/validate_edit')
                assert saved[0]['is_mock'] and saved[0]['demo_id']==name
                assert saved[0]['after']==edited.splitlines()
                rows.append({'demo_id':name,'is_mock':True,'translate':'PASS','candidate':'PASS','edit_validate_save':'PASS'})
            artifacts=[json.loads(p.read_text()) for p in Path(directory).glob('*.json')]
        finally:app.close()
    Path('docs/phase2b/mock-live-results.json').write_text(json.dumps({'is_mock':True,'real_llm_generation':False,'results':rows},ensure_ascii=False,indent=2)+'\n')
    Path('docs/phase2b/mock-experiments.json').write_text(json.dumps({'is_mock':True,'real_llm_generation':False,'artifacts':artifacts},ensure_ascii=False,indent=2)+'\n')
    print('Mock Gradio e2e: PASS (two demos; real BLT bridge; no live LLM)')
if __name__=='__main__':main()
