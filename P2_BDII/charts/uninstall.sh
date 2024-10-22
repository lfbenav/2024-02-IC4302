#!/bin/bash
helm list
helm uninstall application
sleep 10
helm uninstall databases
sleep 10
helm uninstall bootstrap
sleep 10