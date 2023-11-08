# netology_pd73_webpy_celery_hw

## Подготовка файла с переменными окружения
В директории проекта создать файл `.env` со следующими переменными окружения:
```
APP_NAME=netology_pd73_webpy_celery_hw
NGINX_HOST_ADDR_PORT=127.0.0.1:80
HTTP_SRV_URL=http://127.0.0.1/
```
`APP_NAME=netology_pd73_webpy_celery_hw` имя приложения для Flask и Celery

`NGINX_HOST_ADDR_PORT=127.0.0.1:80` адрес и порт, по которым будет доступен веб-сервер на хосте

`HTTP_SRV_URL=http://127.0.0.1/` URL веб-сервера, который будет подставляться в ссылку на выходной файл в результат задачи

## Запуск контейнеров для приложения
Из директории проекта выполнить:
```bash
sudo docker compose up -d
```