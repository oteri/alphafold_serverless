"""Main module invoked by runpod platform."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import runpod  # type: ignore
from absl import logging  # type: ignore # [import-error]
from cloudflare_io import CloudStorageClient
from cloudpathlib import S3Path  # type: ignore

from src import io_utils
from src.prediction import run_prediction

# WORKDIR and PARAM_DIR are usually set by runpod at running time
WORKDIR = os.environ.get("WORKDIR", "/data/")
PARAM_DIR = os.environ.get("PARAM_DIR", "/data/")

logging.set_verbosity(logging.INFO)

logging.debug(f"WORKDIR:{WORKDIR}")
logging.debug(f"PARAM_DIR:{PARAM_DIR}")


def handler(event) -> str:
    """Function invoked by runpod."""
    job_id = event["id"]
    job_dir = Path(tempfile.mkdtemp(prefix=job_id, dir=Path(WORKDIR)))
    logging.debug(f"job_dir:{job_dir}")
    event_input = event["input"]
    msa_file_path = None
    client = None
    if "msa" in event_input:
        content = event_input["msa"]
        msa_file_path = io_utils.create_input_file(content=content, job_dir=job_dir)
    elif "s3" in event_input:
        msa_input = event_input["s3"]
        bucket_name = S3Path(cloud_path=msa_input).bucket
        bucket_name = f"s3://{bucket_name}"
        client = CloudStorageClient(bucket_name=bucket_name)
        msa_file_path = client.download_file(
            object_key=msa_input,
            destination_name=job_dir,
        )
    else:
        raise ValueError(
            "You must supply either the content of a MSA (max 20MB) or the S3 path of the file.",
        )

    logging.debug(f"msa_file_path:{msa_file_path}")

    run_prediction(
        precomputed_msa=msa_file_path,
        output_dir=job_dir,
        data_dir=PARAM_DIR,
    )

    if "s3" in event_input:
        ranked_files = Path(job_dir) / "msa"
        fns = []
        for i, file in enumerate(ranked_files.glob("ranked_*.pdb")):
            fn = f"{job_id}_{i}.pdb"
            client.upload_file(local_file_path=str(file), object_key=fn)
            fns.append(fn)
        return json.dumps({"structure": ",".join(fns)})
    output_file_path = Path(job_dir) / "msa" / "ranked_0.pdb"
    output_content = io_utils.read_output_content(
        output_file_path=str(output_file_path),
    )
    return json.dumps({"structure": output_content})


runpod.serverless.start({"handler": handler})
