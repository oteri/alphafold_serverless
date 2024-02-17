FROM francescooteri/af2_msa:dev

RUN apt-get update && apt-get install -y wget    \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

ENV RUNPOD_DEBUG_LEVEL=DEBUG
ENV PARAM_DIR=/models
WORKDIR $PARAM_DIR/params
RUN wget -qO- https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar| tar xf - --no-same-owner

WORKDIR /app
ADD af2_serverless.yaml .
RUN micromamba install --prefix=/app/env/ -f af2_serverless.yaml -y

ADD *.py .

ADD start.sh .
CMD ["/bin/bash", "/app/start.sh"]
