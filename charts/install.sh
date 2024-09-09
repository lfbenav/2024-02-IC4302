#!/bin/bash
cd bootstrap
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install bootstrap bootstrap
sleep 20

cd monitoring-stack
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install monitoring-stack monitoring-stack
sleep 20

cd databases
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install databases databases
sleep 60

cd app
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install app app
sleep 20

cd grafana-config
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install grafana-config grafana-config

# Función para comprobar que MariaDB esté lista
wait_for_mariadb() {
  echo "Esperando que MariaDB esté lista..."
  while true; do
    status=$(kubectl get pods -l app.kubernetes.io/name=mariadb -o jsonpath="{.items[0].status.phase}")
    if [ "$status" == "Running" ]; then
      echo "MariaDB está lista."
      break
    else
      echo "Esperando que MariaDB esté lista..."
      sleep 10
    fi
  done
}

# Función para comprobar que Postgresql esté listo
wait_for_postgresql() {
  echo "Esperando que Postgresql esté lista..."
  while true; do
    status=$(kubectl get pods -l app.kubernetes.io/name=postgresql -o jsonpath="{.items[0].status.phase}")
    if [ "$status" == "Running" ]; then
      echo "Postgresql está listo."
      break
    else
      echo "Esperando que Postgresql esté lista..."
      sleep 10
    fi
  done
}

# Llamar a la función de espera
wait_for_postgresql
wait_for_mariadb

# Ejecutar el contenedor para cargar datos desde CSV
echo "Ejecutando contenedor para cargar datos desde CSV..."
cd LoadData
rm -rf Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install load-data LoadData

# Función para comprobar que ElasticSearch esté listo
wait_for_elasticsearch() {
  echo "Esperando que ElasticSearch esté lista..."
  while true; do
    status=$(kubectl get pods -l app.kubernetes.io/name=elasticsearch -o jsonpath="{.items[0].status.phase}")
    if [ "$status" == "Running" ]; then
      echo "ElasticSearch está lista."
      break
    else
      echo "Esperando que ElasticSearch esté listo..."
      sleep 10
    fi
  done
}

wait_for_elasticsearch

# Ejecutar el script para crear los indices de elasticsearch
echo "Se crean los indices de elasticsearch..."
bash ./loadElasticIndexes.sh
echo "Los indices de elasticsearch se crearon..."