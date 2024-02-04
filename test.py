import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError


# Load environment variables
load_dotenv()

def download_file_from_r2(bucket_name, object_key, destination_path):
    try:
        access_key = os.getenv('MINIO_ACCESS_KEY')
        secret_key = os.getenv('MINIO_SECRET_KEY')
        endpoint_url = os.getenv('MINIO_SERVER_URL')
        # Check if credentials are loaded
        if not access_key or not secret_key:
            raise Exception("R2 credentials are missing")

        # Initialize a session using Cloudflare R2 credentials
        session = boto3.session.Session()
        s3 = session.client(
            service_name='s3',
            endpoint_url=endpoint_url,  
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        # Download the file
        s3.download_file(bucket_name, object_key, destination_path)
        print(f"File {object_key} downloaded successfully to {destination_path}")
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"An error occurred: {e}")

def upload_file_to_r2(local_file_path, bucket_name, object_key):
    try:
        access_key = os.getenv('MINIO_ACCESS_KEY')
        secret_key = os.getenv('MINIO_SECRET_KEY')
        endpoint_url = os.getenv('MINIO_SERVER_URL')

        # Check if credentials are loaded
        if not access_key or not secret_key:
            raise Exception("R2 credentials are missing")

        # Initialize a session using Cloudflare R2 credentials
        session = boto3.session.Session()
        s3 = session.client(
            service_name='s3',
            endpoint_url=endpoint_url,  
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        # Upload the file
        s3.upload_file(local_file_path, bucket_name, object_key)
        print(f"File {local_file_path} uploaded successfully as {object_key} in {bucket_name} bucket")
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
bucket = os.getenv('MINIO_BUCKET_NAME')
fn = '7FC7_1_ciaone.fasta'
dest=f'/home/oteri/Documents/personal_projects/AF/alphafold_serverless_gui/{fn}'
#download_file_from_r2(bucket,fn ,dest)
upload_file_to_r2(fn, bucket, fn)

