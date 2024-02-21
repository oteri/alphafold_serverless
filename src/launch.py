"""Submits AF2 pipeline to RunPod and saves the output."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

import requests  # type: ignore
from cloudflare_io import CloudStorageClient  # type: ignore
from cloudpathlib import S3Path  # type: ignore
from dotenv import load_dotenv  # type: ignore

# Constants
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(verbose=True)


def parse_arguments() -> argparse.Namespace:
    """Parses command line arguments."""
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
    return parser.parse_args()


def read_msa_file(file_path: str) -> dict[str, str]:
    """Reads the MSA file content or references its S3 path."""
    if file_path.startswith("s3://"):
        return {"s3": file_path}

    msa_file_size = os.path.getsize(file_path)
    if msa_file_size > MAX_FILE_SIZE_BYTES:
        logger.error(
            "Error: MSA file size exceeds the maximum allowed size of %dMB. "
            "Consider uploading your file to a bucket.",
            MAX_FILE_SIZE_MB,
        )
        sys.exit()

    with open(file_path, encoding="utf-8") as file:
        msa_content = file.read()
    return {"msa": msa_content}


def submit_job(url: str, payload: dict, headers: dict) -> str:
    """Submits the job to RunPod and returns the job ID."""
    response = requests.post(url, json=payload, headers=headers, timeout=1000)
    response.raise_for_status()
    response_dict = json.loads(response.text)
    return response_dict["id"]


def check_job_status(url: str, headers: dict) -> tuple[str, dict]:
    """Checks the status of the job."""
    response = requests.get(url, headers=headers, timeout=1000)
    response.raise_for_status()
    response_dict = json.loads(response.text)
    return response_dict["status"], response_dict


def main() -> None:
    """Main function."""
    args = parse_arguments()

    input_data = read_msa_file(args.msa)
    payload = {"input": input_data}

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {os.environ.get('RUNPOD_API_TOKEN')}",
    }

    url = f"https://api.runpod.ai/v2/{args.endpointId}/run"
    logger.info("Submitting job")
    job_id = submit_job(url, payload, headers)
    logger.info("Job ID: %s", job_id)

    status_url = f"https://api.runpod.ai/v2/{args.endpointId}/status/{job_id}"

    while True:
        status, response_dict = check_job_status(status_url, headers)
        if status not in ["FAILED", "COMPLETED"]:
            print("Status not specified", status)
            break

        if status == "FAILED":
            logger.error("Job failed")
            logger.error("Error: %s", response_dict)
            break

        if status == "COMPLETED":
            logger.info("Job successfully completed")
            is_bucket = args.msa.startswith("s3://")
            if is_bucket:
                fn_names = response_dict["output"].split(",")
                handle_completed_job_bucket(fn_msa=args.msa, fn_names=fn_names)
            else:
                response_output_dict = json.loads(response_dict["output"])
                content = response_output_dict["structure"]
                handle_completed_job_content(
                    job_id=job_id,
                    fn_output=args.output,
                    content=content,
                )
            break

        time.sleep(1)
        print(".", end="")


def handle_completed_job_bucket(fn_msa: str | S3Path, fn_names: list[str]) -> None:
    """Handles the completion of a job by downloading output files from a Cloudflare R2 bucket.

    This function iterates over a list of file names and downloads each file from the specified
    Cloudflare R2 bucket to a local directory.

    Args:
        fn_msa (Union[str, S3Path]): The cloud path of the MSA file, used to determine the bucket
                                    name.
        fn_names (List[str]): A list of file names (object keys) to be downloaded from the bucket.
    """
    s3path = S3Path(cloud_path=fn_msa)
    bucket_name = s3path.bucket
    client = CloudStorageClient(bucket_name=bucket_name)
    for obj_name in fn_names:
        client.download_file(object_key=obj_name, destination_name=obj_name)


def handle_completed_job_content(job_id: str, fn_output: str, content: str) -> None:
    """Handles the completion of a job by writing the provided content to an output file.

    This function writes the specified content to an output file.
    If the `fn_output` parameter is not provided, the file name is generated using the `job_id`
    with a `.pdb` extension.
    If `fn_output` is provided, it is used as the file name directly. The content is written in
    UTF-8 encoding.

    Args:
        job_id (str): The job identifier, used to generate the output file name if `fn_output`
                        is not provided.
        fn_output (str): The name of the output file. If None, the file name is generated from
                        the `job_id`.
        content (str): The content to be written to the output file.
    """
    output_file = f"{job_id}.pdb" if fn_output is None else fn_output
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(content)


if __name__ == "__main__":
    main()
