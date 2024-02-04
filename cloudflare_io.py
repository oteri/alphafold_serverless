import os
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError


# Load environment variables
load_dotenv(verbose=True)

def download_file_from_r2(bucket_name:str, object_key:str, destination_path:str|Path)->None:
    """Download an object from a cloudflare bucket on the local file system.

    Args:
        bucket_name (str): name of the bucket with the file.
        object_key (str): name of the object ( i.e. file name ) to  download.
        destination_path (str|Path): destination of the downloaded object.

    Raises:
        Exception: _description_
    """
    try:
        access_key = os.environ['BUCKET_ACCESS_KEY_ID']
        secret_key = os.environ['BUCKET_SECRET_ACCESS_KEY']
        endpoint_url = os.environ['BUCKET_ENDPOINT_URL']
        # Check if credentials are loaded
        if not access_key or not secret_key:
            raise Exception("R2 credentials are missing")

        # Initialize a session using Cloudflare R2 credentials
        session = boto3.session.Session()
        s3 = session.client(
            service_name='s3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        # Download the file
        s3.download_file(bucket_name, object_key, destination_path)
        print(f"File {object_key} downloaded successfully to {destination_path}")
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"An error occurred: {e}")

