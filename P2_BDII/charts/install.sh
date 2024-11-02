#!/bin/bash

cd bootstrap
rm -rf Chart.lock
helm dependency update
cd ..
helm upgrade --install bootstrap bootstrap

sleep 10

cd databases
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install databases databases

sleep 60

helm upgrade --install application application

sleep 120

kubectl port-forward svc/flask-nodeport 5005:5005