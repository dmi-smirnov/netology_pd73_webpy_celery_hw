FROM python:3.10.12

WORKDIR /usr/src/app

COPY ./app/celery_app.py .
COPY ./app/requirements_celery.txt .
COPY ./app/EDSR_x2.pb .

RUN apt update
RUN apt -y install libgl1-mesa-glx
RUN pip install -r requirements_celery.txt

CMD celery --app celery_app.celery_app worker