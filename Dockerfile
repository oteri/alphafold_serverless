FROM francescooteri/af2_msa:latest

ENV RUNPOD_DEBUG_LEVEL=DEBUG
RUN micromamba run -p /app/env/ pip3 install --upgrade --no-cache-dir runpod

RUN cd /app/ && micromamba run -p /app/env/ pip3 install -e alphafold_MSA

WORKDIR /app

ADD handler.py .
ADD start.sh .

CMD ["/bin/bash", "/app/start.sh"]
