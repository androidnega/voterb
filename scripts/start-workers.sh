#!/usr/bin/env bash
# Start Redis (if local) + 6 Celery worker processes for VoteBridge SMS / background jobs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
cd "$BACKEND"

if [[ -f "venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
elif [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-$REDIS_URL}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-$REDIS_URL}"
export CELERY_WORKER_CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-6}"
export CELERY_TASK_ALWAYS_EAGER="${CELERY_TASK_ALWAYS_EAGER:-0}"

if command -v redis-cli >/dev/null 2>&1; then
  if ! redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
    echo "Redis not responding at $REDIS_URL — attempting to start redis-server…"
    if command -v redis-server >/dev/null 2>&1; then
      redis-server --daemonize yes || true
      sleep 1
    fi
  fi
  if redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
    echo "Redis OK ($REDIS_URL)"
  else
    echo "WARNING: Redis still unreachable. Celery will not process SMS until Redis is up."
  fi
fi

echo "Starting Celery with concurrency=$CELERY_WORKER_CONCURRENCY …"
exec celery -A config worker \
  --loglevel=INFO \
  --concurrency="$CELERY_WORKER_CONCURRENCY" \
  -Q votebridge \
  -n votebridge@%h
