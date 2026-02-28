#!/bin/bash
echo "🚀 Iniciando Migrations..."
python migrate_v4_complete.py

echo "🔥 Iniciando API..."
uvicorn main:app --host 0.0.0.0 --port $PORT
