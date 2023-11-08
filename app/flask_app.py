import io
import os

import flask
from flask import Flask, request
from celery.result import AsyncResult as CeleryAsyncResult

from celery_app import celery_app, upscale_task


APP_NAME = os.getenv('APP_NAME', 'test')
OUTPUT_FILES_ROUTE = 'processed/'
HTTP_SRV_URL = os.getenv('HTTP_SRV_URL', 'http://127.0.0.1:5000/')

flask_app = Flask(APP_NAME)

class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = ContextTask

@flask_app.route('/upscale/', methods=['POST'])
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

@flask_app.route('/tasks/<task_id>/', methods=['GET'])
def get_task(task_id: str):
    task = CeleryAsyncResult(task_id, app=celery_app)

    if task.status == 'SUCCESS' and task.result:
        task_result =\
            f'{HTTP_SRV_URL}{OUTPUT_FILES_ROUTE}{task_id}.{task.result[1]}'
    else:
        task_result = task.result

    return {
        'status': task.status,
        'result': task_result
    }

@flask_app.route(f'/{OUTPUT_FILES_ROUTE}<file_name>', methods=['GET'])
def get_file(file_name: str):
    file_name_split = file_name.split('.')
    if len(file_name_split) != 2:
        return '', 404
    
    task_id = file_name_split[0]
    task = CeleryAsyncResult(task_id, app=celery_app)

    if not task.status == 'SUCCESS' or not task.result:
        return '', 404

    img_bytes = task.result[0]
    return flask.send_file(
        io.BytesIO(img_bytes),
        download_name=file_name
    )
