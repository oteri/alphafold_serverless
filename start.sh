#!/bin/bash
set -x

export PYTHONUNBUFFERED=1
export LD_LIBRARY_PATH=/app/env/lib/:${LD_LIBRARY_PATH}

cd /app/
micromamba run -p /app/env/ python3 -u /app/handler.py
