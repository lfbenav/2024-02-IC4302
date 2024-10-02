FROM python:3.12.4-slim-bookworm


WORKDIR /app

COPY app/. .

RUN apt-get update -y \
    && apt-get install -y libmariadb-dev build-essential libmemcached-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py" ]