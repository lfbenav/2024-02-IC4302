#!/bin/bash
# $1 is the username
docker login

cd hugging-face-api/app
echo "Running unit tests for Hugging Face API..."
python -m unittest unitTest.py  
cd ../../ 

cd ingest/app
echo "Running unit tests for Ingest..."
python -m unittest unitTest.py 
cd ../../  

cd s3crawler/app
echo "Running unit tests for S3 Crawler..."
python -m unittest unitTest.py  
cd ../../  

cd flask-api/app
echo "Running unit tests for Flask API..."
python -m unittest unitTest.py  
cd ../../  

echo "Fin de los Unit Tests"
echo "------------------------------------------"

cd hugging-face-api
docker build -t $1/hugging-face-api .
docker push $1/hugging-face-api

cd ../ingest
docker build -t $1/ingest .
docker push $1/ingest

cd ../s3crawler
docker build -t $1/s3crawler .
docker push $1/s3crawler

cd ../flask-api
docker build -t $1/flask-api .
docker push $1/flask-api

cd ../ui
docker build -t $1/ui .
docker push $1/ui
