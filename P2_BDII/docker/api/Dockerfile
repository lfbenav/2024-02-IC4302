FROM python:3.12.4-slim-bookworm

WORKDIR /app

COPY app/. .

RUN apt-get update -y \
    && apt-get install -y libpq-dev build-essential libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py" ]