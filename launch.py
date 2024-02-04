import argparse
import json
import logging
import os
import time

import requests
from dotenv import load_dotenv

#Payloads are limited to:
# run 10 MB.
# runsync: 20 MB.
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 # run is being used so, go for 10MB

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--endpointId", help="Endpoint ID for API request")
parser.add_argument("--msa", default="msa.fasta", help="Path to the MSA file")
parser.add_argument("--output", help="Output file name. Default is jpb_id.pdb")
args = parser.parse_args()

url = f"https://api.runpod.ai/v2/{args.endpointId}/run"

# Check the size of the MSA file
msa_file_size = os.path.getsize(args.msa)
if msa_file_size > MAX_FILE_SIZE_BYTES:
    logger.error("Error: MSA file size exceeds the maximum allowed size of 2MB.")
    exit(1)

# Read the content of the MSA file
msa_content = ""
with open(args.msa, "r") as file:
    msa_content = file.read()

payload = {
    "input": {
        "msa": msa_content,
    }
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {os.environ.get('API_TOKEN')}",
}

logger.info("Submitting job")
response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    response_dict = json.loads(response.text)
    job_id = response_dict["id"]
    logger.info("Jobid: %s", job_id)
    url = f"https://api.runpod.ai/v2/{args.endpointId}/status/{job_id}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {os.environ.get('API_TOKEN')}",
    }
    while 1:
        response = requests.get(url, headers=headers)
        response_dict = json.loads(response.text)

        status = response_dict["status"]
        # "IN_QUEUE", "IN_PROGRESS", "FAILED", "COMPLETED",
        if status == "FAILED":
            logger.error("Job failed")
            logger.error("Error:", response.text)
            break
        if status == "COMPLETED":
            logger.info("Job successfully completed")

            output_file = f"{job_id}.pdb" if args.output is None else args.output
            response_output_dict = json.loads(response_dict["output"])
            with open(output_file, "w") as file:
                file.write(response_output_dict["structure"])
            break
        time.sleep(1)  # Pause for 1 second before the next iteration
        print(".", end="")
