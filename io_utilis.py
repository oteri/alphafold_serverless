"""Handles high level I/O operations."""
import os
from typing import Union
import uuid
from cloudflare_io import CloudStorageClient
from pathlib import Path


def create_input_file(content: str, job_dir: Path) -> Path:
    """Save the content of the input to WORKDIR/msa.fasta .

    Args:
        content (str): Text of the MSA
        job_dir (Path): Directory of the running job

    Returns:
        Path: Full path of the saved file.
    """
    msa_file_path = os.path.join(job_dir, "msa.fasta")
    with open(msa_file_path, "w") as file:
        file.write(content)
    return Path(msa_file_path)


def read_output_content(output_file_path: Path) -> str:
    """Read the output file and return it as a string.

    Args:
        output_file_path (Path): path of the output file.

    Returns:
        str: the content of the file.
    """
    with open(output_file_path) as file:
        output_content = file.read()
        return output_content


def download_obj_from_r2(obj_name: str, msa_file_path: Path) -> Path:
    """Downloads some object from a R2 bucket to disk.

    Args:
        obj_name (str): name of the object
        msa_file_path (Path): _description_

    Returns:
        Path: The full path the object hs been dumped to.
    """
    client = CloudStorageClient()
    client.download_file(obj_name, msa_file_path)
    return Path(msa_file_path)


def upload_file_to_r2(file_name: str, object_key: Union[str, None] = None) -> str:
    """Upload a file to an object on a R2 bucket.

    Args:
        file_name (str): Path of the file.
        object_key (str): The object key (i.e., file name) under which the file will be stored in the bucket.
                                If None, a unique name is generated.

    Returns:
        str: the path of the object
    """
    if object_key is None:
        file_extension = Path(file_name).suffix
        object_key = f"{uuid.uuid4()}{file_extension}"
    return CloudStorageClient().upload_file(
        local_file_path=file_name, object_key=object_key
    )
