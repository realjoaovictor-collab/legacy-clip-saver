FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# Always grab the newest yt-dlp on each build, since Instagram changes often
RUN pip install --no-cache-dir -U -r requirements.txt
COPY . .

ENV PORT=10000
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 300 app:app
