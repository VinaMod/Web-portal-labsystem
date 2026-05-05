#!/bin/sh
set -e

echo "[INFO] Loading Docker secrets..."

export SECRET_KEY=$(cat /run/secrets/secret_key)
export JWT_SECRET=$(cat /run/secrets/jwt_secret)
export GOOGLE_CLIENT_SECRET=$(cat /run/secrets/google_client_secret)
export DATABASE_PASSWORD=$(cat /run/secrets/db_password)

echo "[INFO] Rendering .env file..."
echo ${MQL_DB_HOST}

envsubst < /app/.env.template > /app/.env

echo "[INFO] Starting application..."

exec "$@"