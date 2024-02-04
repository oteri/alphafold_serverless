import json
import os
import tempfile
from pathlib import Path
from absl import logging

import runpod

from  prediction import run_prediction_test as run_prediction

import io_utilis


# WORKDIR and PARAM_DIR are usually set by runpod at running time
WORKDIR  = os.environ.get("WORKDIR", "/data/")
PARAM_DIR = os.environ.get("PARAM_DIR", "/data/")

logging.set_verbosity(logging.INFO)

logging.debug(f'WORKDIR:{WORKDIR}')
logging.debug(f'PARAM_DIR:{PARAM_DIR}')

def handler(event):
    job_dir = Path(tempfile.mkdtemp(dir=Path(WORKDIR)))
    logging.debug(f'job_dir:{job_dir}')
    event_input = event["input"]
    msa_file_path = None
    if "msa" in event_input:
        content = event_input["msa"]
        msa_file_path = io_utilis.create_input_file(content=content, job_dir=job_dir)
    elif "s3" in event_input:
        s3_input = event_input["s3"]
        msa_file_path = io_utilis.download_file_from_r2(fn_name=s3_input, job_dir=job_dir)
    else:
        raise ValueError('You must supply either the content of a MSA (max 20MB) or the S3 path of the file.')

    logging.debug(f'msa_file_path:{msa_file_path}')

    run_prediction(precomputed_msa=msa_file_path, output_dir=job_dir, data_dir=PARAM_DIR)

    # Since runpod doesn't allow to manage more than 10MB so only the best result is returned.

    output_file_path = Path(job_dir) / "msa" / "ranked_0.pdb"
    output_content = io_utilis.read_output_content(output_file_path=str(output_file_path))

    return json.dumps({"structure": output_content})


runpod.serverless.start({"handler": handler})
