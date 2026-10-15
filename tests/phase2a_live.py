"""Against a running loopback UI: real Gradio events and audio HTTP delivery."""
import io
import json
from pathlib import Path
import httpx
import soundfile as sf
from gradio_client import Client
from hw2_ui.catalog import read_catalog

URL = 'http://127.0.0.1:7860'

def main():
    client = Client(URL, download_files=False, verbose=False, analytics_enabled=False)
    records = []
    config = httpx.get(URL + '/config').json()
    dropdowns = [c['props'] for c in config['components'] if c['type'] == 'dropdown']
    assert dropdowns[2]['filterable'] and dropdowns[2]['value'] == 'SingEdit_EN_01'
    for demo in read_catalog():
        client.predict(demo.language, '全部', api_name='/filter_language')
        result = client.predict(demo.id, api_name='/select_demo')
        assert result[1] == demo.original_lyrics
        assert result[6]['demo_id'] == demo.id
        file = result[2]
        response = httpx.get(file['url'], timeout=20)
        assert response.status_code == 200
        assert response.content[:4] == b'RIFF'
        samples, rate = sf.read(io.BytesIO(response.content), always_2d=True)
        assert len(samples) > 0 and rate == result[6]['assets']['original_audio']['sample_rate']
        ranged = httpx.get(file['url'], headers={'Range': 'bytes=0-127'})
        assert ranged.status_code == 206 and len(ranged.content) == 128
        records.append({'demo_id': demo.id, 'lyrics_match': True, 'http_status': response.status_code,
                        'range_status': ranged.status_code, 'decoded_frames': len(samples),
                        'sample_rate': rate, 'line_count': result[6]['line_count']})
    changed = client.predict('zh', 'Lyric Editing', api_name='/filter_language')
    assert len(changed[0]['choices']) == 2 and changed[7]['language'] == 'zh'
    changed = client.predict('en', 'Melody Control', api_name='/filter_task')
    assert len(changed[0]['choices']) == 2 and changed[2] == '' and not changed[7]['complete']
    try:
        client.predict('invalid-id', api_name='/select_demo')
    except Exception as exc:
        assert 'not in the list of choices' in str(exc)
    else:
        raise AssertionError('Gradio accepted an invalid Dropdown value')
    output = {'url': URL, 'dropdown_filterable': True, 'default': 'SingEdit_EN_01',
              'selections': records, 'language_task_filters': 'PASS', 'invalid_id': 'PASS',
              'browser_listening': '未執行：需使用者透過 Port Forwarding 人工確認'}
    Path('docs/phase2a/live-results.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
