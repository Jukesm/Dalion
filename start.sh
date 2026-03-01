#!/bin/bash
echo "🚀 Iniciando Migrations..."
python migrate_v4_complete.py

echo "🦾 Iniciando RQ Worker em background..."
if [ -z "$REDIS_URL" ]; then
    echo "⚠️ REDIS_URL não configurada. Pulando Worker..."
else
    rq worker pipeline tracking notifications --url $REDIS_URL &
fi

echo "🔥 Iniciando API..."
uvicorn main:app --host 0.0.0.0 --port $PORT
