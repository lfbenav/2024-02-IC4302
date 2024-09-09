FROM python:3.12.4-slim-bookworm

WORKDIR /app

COPY app/. .

RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "flask",  "--app", "app", "run" ]