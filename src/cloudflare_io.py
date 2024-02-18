"""Manages interaction with cloudlfare bucket."""
import os
from pathlib import Path
from typing import Union
import uuid
from cloudpathlib import S3Client, S3Path  # type: ignore
from dotenv import load_dotenv  # type: ignore

# Load environment variables
load_dotenv(verbose=True)


class CloudStorageClient:
    """A client for interacting with Cloudflare R2 cloud storage using cloudpathlib."""

    def __init__(
        self,
        bucket_name: str,
        access_key: Union[str, None] = None,
        secret_key: Union[str, None] = None,
        endpoint_url: Union[str, None] = None,
    ):
        """Initialize CloudStorageClient with cloudpathlib."""
        self.access_key = access_key or os.getenv("BUCKET_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("BUCKET_SECRET_ACCESS_KEY")
        self.endpoint_url = endpoint_url or os.getenv("BUCKET_ENDPOINT_URL")
        self.bucket_name = bucket_name

        if not all(
            [self.access_key, self.secret_key, self.endpoint_url, self.bucket_name]
        ):
            raise OSError("Missing required credentials or bucket information.")

        self.client = S3Client(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url,
        )

        self.bucket = S3Path(f"{self.bucket_name}", client=self.client)

    def download_file(
        self, object_key: str, destination_path: Union[str, Path]
    ) -> None:
        """Downloads a file from a Cloudflare R2 bucket."""
        file_path = self.bucket / object_key
        file_path.download_to(destination=destination_path)
        print(f"File {object_key} downloaded successfully to {destination_path}")

    def upload_file(
        self, local_file_path: Union[str, Path], object_key: Union[str, None] = None
    ) -> str:
        """Uploads a file to a Cloudflare R2 bucket."""
        if object_key is None:
            object_key = str(uuid.uuid1())

        file_path = self.bucket / object_key
        file_path.upload_from(source=local_file_path)
        return object_key


if __name__ == "__main__":
    import tempfile

    bucket_name = "s3://structures"
    storage_client = CloudStorageClient(bucket_name=bucket_name)
    try:
        fn_in = "README.md"
        object_key = storage_client.upload_file(fn_in)
        print(
            f"File {fn_in} uploaded successfully as {object_key} in {bucket_name} bucket"
        )
        # Create a temporary file and close it to avoid locking issues on Windows
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file_path = temp_file.name
        temp_file.close()

        # Download the file to the temporary file path
        storage_client.download_file(
            object_key=object_key, destination_path=temp_file_path
        )
        print(f"File downloaded to temporary file: {temp_file_path}")

    except Exception as e:
        print(f"Error: {e}")
