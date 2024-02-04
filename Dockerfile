FROM francescooteri/af2_msa:dev

ENV RUNPOD_DEBUG_LEVEL=DEBUG
WORKDIR /app
ADD af2_serverless.yaml .
RUN micromamba install --prefix=/app/env/ -f af2_serverless.yaml -y


ADD *.py .
ADD start.sh .

CMD ["/bin/bash", "/app/start.sh"]
