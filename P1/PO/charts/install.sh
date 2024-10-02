#!/bin/bash
cd monitoring-stack
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install monitoring-stack monitoring-stack

sleep 60

cd bootstrap
rm -rf Chart.lock
helm dependency update
cd ..
helm upgrade --install bootstrap bootstrap

sleep 20

cd databases
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install databases databases

sleep 60

# #cd application
# #helm dependency update
# #cd ..
#helm upgrade --install application application

#sleep 60

helm upgrade --install application application

sleep 60

cd grafana-config
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install grafana-config grafana-config

sleep 60

#Port fordward de flask-api-nodeport
sleep 222
kubectl port-forward svc/flask-api-nodeport 5005:5005


