#!/usr/bin/env bash

set -e


cd /opt/rnd/kfc_support_bot/

echo -e "Останавливаем текущие контейнеры проекта..."
docker compose down

echo -e "Выкачиваем изменения из репозитория..."
git pull

COMMIT=`git rev-parse --short HEAD`
LOCAL_USERNAME=$(whoami)

echo -e "Пересобираем контейнеры и запускаем..."
docker compose up -d --build

echo -e "Собираем статику Django..."
docker compose exec web python manage.py collectstatic --no-input --clear

echo -e "Отправляем уведомление в Rollbar..."
curl -H "X-Rollbar-Access-Token: $ROLLBAR_POST_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "production", "revision": "'$COMMIT'", "local_username": "'$LOCAL_USERNAME'"}'

echo -e "Всё готово!"