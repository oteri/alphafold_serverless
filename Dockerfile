FROM francescooteri/af2_msa:dev

RUN apt-get update && apt-get install -y wget    \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

ENV RUNPOD_DEBUG_LEVEL=DEBUG
WORKDIR /app
ADD af2_serverless.yaml .
RUN micromamba install --prefix=/app/env/ -f af2_serverless.yaml -y


ADD *.py .
ADD start.sh .
CMD ["/bin/bash", "/app/start.sh"]
