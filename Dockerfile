FROM python:3.11-slim

# Установка git и других системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://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@github.com/denis5261/NevestaAI_bot.git /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]