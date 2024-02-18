"""Submits AF2 pipeline to RunPod and saves the output."""
import argparse
import json
import logging
import os
import time
from cloudpathlib import S3Path  # type: ignore

import requests  # type: ignore
from dotenv import load_dotenv  # type: ignore

from cloudflare_io import CloudStorageClient

# Payloads are limited to:
# run 10 MB.
# runsync: 20 MB.
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)  # run is being used so, go for 10MB

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(verbose=True)

parser = argparse.ArgumentParser()
parser.add_argument("--endpointId", type=str, help="Endpoint ID for API request")
parser.add_argument(
    "--msa",
    type=str,
    default="msa.fasta",
    help="Path to the MSA file. If the file is on a bucket, the results will be on the same bucket",
)

parser.add_argument(
    "--output",
    type=str,
    help="Output file name. Default is job_id.pdb",
)
args = parser.parse_args()

url = f"https://api.runpod.ai/v2/{args.endpointId}/run"

# Read the content of the MSA file
is_bucket = args.bucket.startswith("s3://")
if is_bucket:
    input = {"s3": args.msa}
else:
    # Check the size of the MSA file
    msa_file_size = os.path.getsize(args.msa)
    if msa_file_size > MAX_FILE_SIZE_BYTES:
        logger.error(
            f"""Error: MSA file size exceeds the maximum allowed size of {MAX_FILE_SIZE_MB}MB.
            Think about uploading your file to a bucket.
            """
        )
        exit(1)

    msa_content = ""
    with open(args.msa) as file:
        msa_content = file.read()
    input = {"msa": msa_content}

payload = {"input": input}


headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {os.environ.get('RUNPOD_API_TOKEN')}",
}

logger.info("Submitting job")
response = requests.post(url, json=payload, headers=headers)
response.raise_for_status()

response_dict = json.loads(response.text)
job_id = response_dict["id"]
logger.info("Jobid: %s", job_id)
url = f"https://api.runpod.ai/v2/{args.endpointId}/status/{job_id}"
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {os.environ.get('RUNPOD_API_TOKEN')}",
}
while 1:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response_dict = json.loads(response.text)

    status = response_dict["status"]
    # "IN_QUEUE", "IN_PROGRESS", "FAILED", "COMPLETED",
    if status == "FAILED":
        logger.error("Job failed")
        logger.error("Error:", response.text)
        break
    if status == "COMPLETED":
        logger.info("Job successfully completed")

        if is_bucket:
            fn_names = response_dict["output"].split(",")
            bucket_name = S3Path(cloud_path=args.msa).bucket
            client = CloudStorageClient(bucket_name=bucket_name)
            for obj_name in fn_names:
                client.download_file(object_key=obj_name, destination_path=obj_name)
        else:
            output_file = f"{job_id}.pdb" if args.output is None else args.output
            response_output_dict = json.loads(response_dict["output"])
            with open(output_file, "w") as file:
                file.write(response_output_dict["structure"])
        break
    time.sleep(1)  # Pause for 1 second before the next iteration
    print(".", end="")
