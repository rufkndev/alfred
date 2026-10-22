#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

case "$1" in
  up)
    [ -d .git ] && git pull --ff-only
    docker compose up -d --build
    docker image prune -f > /dev/null
    ;;
  down) docker compose down ;;
  logs) docker compose logs -f --tail=100 app ;;
  vapid) docker compose run --rm --no-deps app python -m app.push keys ;;
  *) echo "usage: ./alfred.sh up | down | logs | vapid" ;;
esac
