#!/bin/bash
# $1 is the username
docker login

cd loader
docker build -t $1/loader .
docker push $1/loader

cd ../migrador
docker build -t $1/migrador .
docker push $1/migrador

cd ../api
docker build -t $1/api .
docker push $1/api

cd ../ui
docker build -t $1/ui .
docker push $1/ui