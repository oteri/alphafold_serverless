#!/bin/bash
set -x

date
# Check if PARAM_DIR is unset or empty
if [ -z "$PARAM_DIR" ]; then
    PARAM_DIR="/data/"
fi

# Check if the directory exists, and create it if it doesn't
if [ ! -d "$PARAM_DIR/params" ]; then
    mkdir -p "$PARAM_DIR/params"
    echo "Directory $PARAM_DIR created."
    cd $PARAM_DIR/params
    wget -qO- https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar| tar xf - --no-same-owner
fi


cd /app/
export PYTHONUNBUFFERED=1

export LD_LIBRARY_PATH=/app/env/lib/:${LD_LIBRARY_PATH}
micromamba run -p /app/env/ python3 -u /app/handler.py
