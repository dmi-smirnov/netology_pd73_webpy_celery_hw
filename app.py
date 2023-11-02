from functools import cache
import os
import uuid

import flask
from flask import Flask, request
from celery import Celery
from celery.result import AsyncResult as CeleryAsyncResult
import cv2


APP_NAME = __name__
REDIS_HOST_PORT = '6379'
CELERY_BROKER = f'redis://127.0.0.1:{REDIS_HOST_PORT}/1'
CELERY_BACKEND = f'redis://127.0.0.1:{REDIS_HOST_PORT}/2'
FILES_DIR_PATH = 'files'
MODEL_FILE_PATH = 'EDSR_x2.pb'
OUTPUT_FILES_ROUTE = 'processed/'
HTTP_SRV_URL = 'http://127.0.0.1:5000/'

app = Flask(APP_NAME)
celery = Celery(
    APP_NAME,
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND
)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

@cache
def get_scaler():
    scaler = cv2.dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(MODEL_FILE_PATH)
    scaler.setModel('edsr', 2)
    return scaler

@celery.task
def upscale_task(input_img_file_path: str) -> str:
    image = cv2.imread(input_img_file_path)
    result = get_scaler().upsample(image)
    img_file_extension = input_img_file_path.split('.')[-1]
    output_img_file_name = f'{uuid.uuid4()}.{img_file_extension}'
    output_img_file_path = os.path.join(FILES_DIR_PATH, output_img_file_name)
    cv2.imwrite(output_img_file_path, result)

    os.remove(input_img_file_path)

    output_img_url =\
        HTTP_SRV_URL + OUTPUT_FILES_ROUTE + output_img_file_name
    return output_img_url

@app.route('/upscale/', methods=['POST'])
def upscale():
    img = request.files.get('img')
    if not img:
        return {
            'status': 'error',
            'description': 'File "img" not found in this HTTP request.'
        }, 400
    
    img_file_name = img.filename
    if not img_file_name:
        return '', 400
    img_file_extension = img_file_name.split('.')[-1]
    img_file_name = f'{uuid.uuid4()}.{img_file_extension}'
    img_file_path = os.path.join(FILES_DIR_PATH, img_file_name)
    if not os.path.exists(FILES_DIR_PATH):
        os.makedirs(FILES_DIR_PATH)
    img.save(img_file_path)

    task = upscale_task.delay(img_file_path)
    return {'task_id': task.id}

@app.route('/tasks/<task_id>/', methods=['GET'])
def get_task(task_id: str):
    task = CeleryAsyncResult(task_id, app=celery)
    return {
        'status': task.state,
        'result': task.result
    }

@app.route(f'/{OUTPUT_FILES_ROUTE}<file_name>', methods=['GET'])
def get_file(file_name: str):
    try:
        return flask.send_from_directory(FILES_DIR_PATH, file_name)
    except FileNotFoundError:
        return '', 404
