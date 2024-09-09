#!/bin/bash
# $1 is the username
docker login

cd FlaskApp

docker build -t $1/flask-example .
docker push $1/flask-example

cd ..

# Construir y subir la imagen de LoadData
cd LoadData

docker build -t $1/load-data .
docker push $1/load-data

cd ..