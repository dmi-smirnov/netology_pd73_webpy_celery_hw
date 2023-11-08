FROM python:3.10.12

WORKDIR /usr/src/app

COPY ./app/flask_app.py .
COPY ./app/celery_app.py .
COPY ./app/requirements_flask_gunicorn.txt .

RUN apt update
RUN apt -y install libgl1-mesa-glx
RUN pip install -r requirements_flask_gunicorn.txt

CMD gunicorn flask_app:flask_app -b 0.0.0.0:80