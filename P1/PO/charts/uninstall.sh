#!/bin/bash
helm list
helm uninstall application
sleep 15
helm uninstall databases
sleep 60
helm uninstall bootstrap
sleep 15
helm uninstall grafana-config
sleep 15
helm uninstall monitoring-stack
sleep 15