#!/bin/bash
# $1 is the username
docker login

cd loader/app
echo "Running unit tests for loader..."
python -m unittest unitTests.py 
cd ../../  

cd migrador/app
echo "Running unit tests for migrador..."
python -m unittest unitTests.py  
cd ../../  

cd api/app
echo "Running unit tests for API..."
python -m unittest unitTests.py  
cd ../../  

echo "Fin de los Unit Tests"
echo "------------------------------------------"

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







#cd api
#docker build -t $1/api .
#docker push $1/api
# cd ui
# docker build -t $1/ui .
# docker push $1/ui
