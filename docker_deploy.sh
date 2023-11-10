#!/usr/bin/env bash

set -e


echo -e "Выкачиваем изменения из репозитория..."
git pull

COMMIT=`git rev-parse --short HEAD`
LOCAL_USERNAME=$(whoami)

echo -e "Пересобираем контейнер web и запускаем..."
docker compose up -d --no-deps --force-recreate web

echo -e "Собираем статику Django..."
docker compose exec web python manage.py collectstatic --no-input --clear -v 0

echo -e "Отправляем уведомление в Rollbar..."
curl -H "X-Rollbar-Access-Token: $ROLLBAR_POST_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "'$ROLLBAR_ENV'", "revision": "'$COMMIT'", "local_username": "'$LOCAL_USERNAME'"}'

echo -e "\nВсё готово!"
