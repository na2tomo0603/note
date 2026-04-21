FROM python:3.11-slim

WORKDIR /app

# Playwright に必要なシステム依存
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium ブラウザをインストール
RUN playwright install chromium --with-deps

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
