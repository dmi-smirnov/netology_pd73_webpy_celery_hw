import io
import time

import requests
from PIL import Image

def test_upscale():
    HTTP_SRV_URL = 'http://127.0.0.1:80/'
    IMG_FILE_PATH = 'tests/lama_300px.png'
    TASK_REQUEST_DELAY_SEC = 1
    TASK_REQUESTS_MAX = 120

    with Image.open(IMG_FILE_PATH) as img:
        orig_img_width, orig_img_height = img.size

    with open(IMG_FILE_PATH, 'rb') as img_file:
        upscale_resp = requests.post(f'{HTTP_SRV_URL}upscale',
                                     files={'img': img_file})
    assert upscale_resp.status_code == 200
    
    upscale_resp_json = upscale_resp.json()
    assert upscale_resp_json

    assert isinstance(upscale_resp_json, dict)
    task_id = upscale_resp_json.get('task_id')
    assert task_id

    task_status = ''
    req_count = 0
    task_resp_json = dict()
    while task_status != 'SUCCESS':
        task_resp = requests.get(f'{HTTP_SRV_URL}tasks/{task_id}')
        assert task_resp.status_code == 200

        task_resp_json = task_resp.json()
        assert isinstance(task_resp_json, dict)

        task_status = task_resp_json.get('status')
        assert task_status != None

        assert req_count < TASK_REQUESTS_MAX
        req_count += 1

        time.sleep(TASK_REQUEST_DELAY_SEC)
        
    task_result = task_resp_json.get('result')
    assert task_result

    result_file_resp = requests.get(task_result)
    assert result_file_resp.status_code == 200

    result_file_bytes = result_file_resp.content
    result_img_width, result_img_height =\
        Image.open(io.BytesIO(result_file_bytes)).size
    
    assert result_img_width == orig_img_width * 2
    assert result_img_height == orig_img_height * 2
