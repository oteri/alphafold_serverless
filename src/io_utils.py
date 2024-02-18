"""Handles high level I/O operations."""
import os
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
