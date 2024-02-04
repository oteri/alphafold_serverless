FROM af2_msa:latest

ENV RUNPOD_DEBUG_LEVEL=DEBUG
WORKDIR /app
ADD af2_serverless.yaml .
RUN micromamba install --prefix=/app/env/ -f af2_serverless.yaml -y


ADD handler.py .
ADD start.sh .

CMD ["/bin/bash", "/app/start.sh"]
