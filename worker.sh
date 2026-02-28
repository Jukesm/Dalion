#!/bin/bash
echo "🦾 Iniciando Workers (Pipeline & Tracking)..."
# Inicia dois workers para cobrir todas as filas
rq worker pipeline tracking notifications --url $REDIS_URL
