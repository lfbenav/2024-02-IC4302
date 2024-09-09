FROM python:3.12.4-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY load_data.py .
COPY movies.csv .
COPY ratings.csv .

# Ejecuta el script para cargar los datos
CMD ["python", "load_data.py"]