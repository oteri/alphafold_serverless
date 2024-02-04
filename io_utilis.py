import os
from pathlib import Path
def create_input_file(event,job_dir:Path)-> Path:
    # Save event.msa to WORKDIR/msa.fasta
    msa_file_path = os.path.join(job_dir, "msa.fasta")
    with open(msa_file_path, "w") as file:
        file.write(event["input"]["msa"])
    return Path(msa_file_path)


def read_output_content(output_file_path:Path)->str:
    """Read the output file and return it as a string.

    Args:
        output_file_path (Path): path of the output file.

    Returns:
        str: the content of the file.
    """
    with open(output_file_path, "r") as file:
        output_content = file.read()
        return output_content