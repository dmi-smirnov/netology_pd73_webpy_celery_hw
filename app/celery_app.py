from functools import cache
import os
import numpy

from celery import Celery
import cv2


APP_NAME = os.getenv('APP_NAME', 'test')
REDIS_ADDR = os.getenv('REDIS_ADDR', '127.0.0.1')
REDIS_PORT = '6379'
CELERY_BROKER = f'redis://{REDIS_ADDR}:{REDIS_PORT}/1'
CELERY_BACKEND = f'redis://{REDIS_ADDR}:{REDIS_PORT}/2'
MODEL_FILE_PATH = 'EDSR_x2.pb'

celery_app = Celery(
    APP_NAME,
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND
)

@cache
def get_scaler():
    scaler = cv2.dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(MODEL_FILE_PATH)
    scaler.setModel('edsr', 2)
    return scaler

@celery_app.task
def upscale_task(input_img_bytes: bytes, img_file_extension: str) -> tuple[bytes, str]:
    input_img_numpy_array =\
        numpy.asarray(bytearray(input_img_bytes), dtype='uint8')
    image = cv2.imdecode(input_img_numpy_array, cv2.IMREAD_COLOR)

    result = get_scaler().upsample(image)

    output_img_encode = cv2.imencode('.png', result)[1]
    output_img_data_encode = numpy.array(output_img_encode)
    output_img_bytes = output_img_data_encode.tobytes()

    return (output_img_bytes, img_file_extension)
