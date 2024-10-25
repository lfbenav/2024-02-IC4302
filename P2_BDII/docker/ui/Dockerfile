FROM python:3.12.4-slim-bookworm


WORKDIR /app

COPY app/. .

RUN apt-get update -y \
    && apt-get install -y libmariadb-dev build-essential libmemcached-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py" ]

# Use Nginx to serve static files
FROM nginx:alpine

# Set the working directory inside the container
WORKDIR /usr/share/nginx/html

# Remove the default Nginx files
RUN rm -rf ./*

# Copy all your static files (HTML, CSS, JS) into the Nginx web root
COPY ./app .

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]