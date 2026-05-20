#!/usr/bin/env sh
set -ex
trap exit TERM
if [ -z "$ALEMBIC_CONFIG" ]; then
  export ALEMBIC_CONFIG=/shaman/alembic.ini
fi
pecan populate ./config/dev.py
CURRENT=$(alembic current)
if [ -z "$CURRENT" ]; then
  echo "No current revision; assuming no migration necessary"
  alembic stamp head
else
  echo "Current revision: $CURRENT - will attempt to migrate"
  alembic upgrade head
fi
if [ "$GUNICORN" = "false" ]; then
  pecan serve ./config/run.py
else
  gunicorn_pecan ./config/run.py
fi