#!/usr/bin/env bash

set -euo pipefail

if [[ $1 == "docker-start" ]]; then
  shift

  if [[ $1 == "runserver-plus" ]]; then
    exec python3 manage.py runserver_plus "0:8000" --nopin --nostatic
  elif [[ $1 == "gunicorn" ]]; then
    exec gunicorn pr_review_benchmark.wsgi:application
  elif [[ $1 == "celery" ]]; then
    exec celery -A pr_review_benchmark worker --loglevel=info
  elif [[ $1 == "watchmedo-celery" ]]; then
    exec \
      watchmedo \
      auto-restart \
      --directory=pr_review_benchmark \
      --pattern=*.py \
      --recursive \
      -- \
      celery -A pr_review_benchmark worker --loglevel=info
  elif [[ $1 == "celery-beat" ]]; then
    exec celery -A pr_review_benchmark beat --loglevel=info
  elif [[ $1 == "watchmedo-celery-beat" ]]; then
    exec \
      watchmedo \
      auto-restart \
      --directory=pr_review_benchmark \
      --pattern=*.py \
      --recursive \
      -- \
      celery -A pr_review_benchmark beat --loglevel=info
  elif [[ $1 == "tailwind-watch" ]]; then
    npm ci
    exec npm run tailwind:watch
  elif [[ $1 == "heroku-gunicorn-celery-celery-beat" ]]; then
    # Hack to run gunicorn, celery, and celery-beat in a single dyno
    # https://help.heroku.com/CTFS2TJK/how-do-i-run-multiple-processes-on-a-dyno
    trap '' SIGTERM; \
      gunicorn pr_review_benchmark.wsgi:application & \
      celery -A pr_review_benchmark worker --loglevel=info & \
      celery -A pr_review_benchmark beat --loglevel=info & \
      wait -n; \
      kill -SIGTERM -$$; \
      wait
  fi
fi

exec "$@"
