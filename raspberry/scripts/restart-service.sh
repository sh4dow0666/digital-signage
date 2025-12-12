#!/bin/bash

PID=$1

echo "Kill process with pid: $1"
kill -9 $1

cd /opt/digital-signage/
python3 gestion_raspberry.py &