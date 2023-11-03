from functools import cache
import io
import numpy

import flask
from flask import Flask, request
from celery import Celery
from celery.result import AsyncResult as CeleryAsyncResult
import cv2


APP_NAME = __name__
REDIS_HOST_PORT = '6379'
CELERY_BROKER = f'redis://127.0.0.1:{REDIS_HOST_PORT}/1'
CELERY_BACKEND = f'redis://127.0.0.1:{REDIS_HOST_PORT}/2'
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
def upscale_task(input_img_bytes: bytes, img_file_extension: str) -> tuple[bytes, str]:
    input_img_numpy_array =\
        numpy.asarray(bytearray(input_img_bytes), dtype='uint8')
    image = cv2.imdecode(input_img_numpy_array, cv2.IMREAD_COLOR)

    result = get_scaler().upsample(image)

    output_img_encode = cv2.imencode('.png', result)[1]
    output_img_data_encode = numpy.array(output_img_encode)
    output_img_bytes = output_img_data_encode.tobytes()

    return (output_img_bytes, img_file_extension)

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

    task = upscale_task.delay(img.read(), img_file_extension)

    return {'task_id': task.id}

@app.route('/tasks/<task_id>/', methods=['GET'])
def get_task(task_id: str):
    task = CeleryAsyncResult(task_id, app=celery)

    if task.status == 'SUCCESS' and task.result:
        task_result =\
            f'{HTTP_SRV_URL}{OUTPUT_FILES_ROUTE}{task_id}.{task.result[1]}'
    else:
        task_result = task.result

    return {
        'status': task.status,
        'result': task_result
    }

@app.route(f'/{OUTPUT_FILES_ROUTE}<file_name>', methods=['GET'])
def get_file(file_name: str):
    file_name_split = file_name.split('.')
    if len(file_name_split) != 2:
        return '', 404
    
    task_id = file_name_split[0]
    task = CeleryAsyncResult(task_id, app=celery)

    if not task.status == 'SUCCESS' or not task.result:
        return '', 404

    img_bytes = task.result[0]
    return flask.send_file(
        io.BytesIO(img_bytes),
        download_name=file_name
    )
