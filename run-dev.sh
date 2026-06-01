#!/usr/bin/env bash
# Dev stack: bind-mounted source + Vite HMR + uvicorn --reload
#   Frontend: http://localhost:3000 (also http://localhost:3001)
#   Admin:    http://localhost:3003
#   API:      http://localhost:8000
# Plain `docker compose up` (no -f docker-compose.dev.yml) is production: 3000 / 3002, no live reload.
set -e
cd "$(dirname "$0")"
# docker-compose.override.yml enables dev mode for plain `docker compose up` too
docker compose up "$@" -d
