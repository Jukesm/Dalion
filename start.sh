#!/bin/bash
echo "🚀 Iniciando Migrations..."
python migrate_v4_complete.py

echo "🦾 Iniciando RQ Worker em background..."
# Inicia os workers em background para não travar a API
rq worker pipeline tracking notifications --url $REDIS_URL &

echo "🔥 Iniciando API..."
uvicorn main:app --host 0.0.0.0 --port $PORT
