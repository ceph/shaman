#!/usr/bin/env bash
set -euo pipefail

# Build a production config by importing config/dev.py via path and overriding
# only what we need with environment variables from OpenShift.


cd "${APP_HOME:-/opt/app}" || true
mkdir -p config

cat > config/prod.py <<'PY'
import os, pathlib, importlib.util

# Load config/dev.py by file path (no package import needed)
_cfg_path = pathlib.Path(__file__).with_name('dev.py')
_spec = importlib.util.spec_from_file_location("dev_cfg", _cfg_path)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)


server = dict(getattr(base, 'server', {}))
if not server:
    server = {'host': '0.0.0.0', 'port': '8080'}  # default if dev.py doesn’t define it

app = dict(getattr(base, 'app', {}))
app['debug'] = False

# Runtime DB config used by the app
sqlalchemy = {
    'url'  : os.getenv('DATABASE_URL', 'postgresql+psycopg2://shaman:shaman@postgres:5432/shaman'),
    'echo' : False,
}

# API auth and optional GitHub secret (shaman/auth.py checks api_user/api_key)
api_user = os.getenv('SHAMAN_API_USER', getattr(base, 'api_user', ''))
api_key  = os.getenv('SHAMAN_API_KEY',  getattr(base, 'api_key',  ''))
_gs = os.getenv('GITHUB_SECRET', '')
github_secret = _gs.encode('utf-8') if _gs else getattr(base, 'github_secret', None)

# Health behavior & chacra TLS verify
health_check_retries = int(os.getenv('HEALTH_CHECK_RETRIES', str(getattr(base, 'health_check_retries', 3))))
chacra_verify_ssl    = os.getenv('CHACRA_VERIFY_SSL', str(getattr(base, 'chacra_verify_ssl', 'false'))).lower() == 'true'

# RabbitMQ (pika) URL; define both names to satisfy any code path
_bus = os.getenv('RABBITMQ_URL', '')
bus_url       = _bus or getattr(base, 'bus_url', '')
rabbitmq_url  = _bus or getattr(base, 'rabbitmq_url', '')
PY

# Hand over to Pecan with the generated config
exec pecan serve "${APP_HOME}/config/prod.py"
