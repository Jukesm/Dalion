FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Garante permissões de execução para os scripts
RUN chmod +x start.sh worker.sh

# Render dinamicamente define a porta via variável $PORT
ENV PORT=8000
EXPOSE 8000

CMD ["./start.sh"]
