"""Manages interaction with cloudlfare bucket."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from cloudpathlib import S3Client, S3Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(verbose=True)


class CloudStorageClient:
    """A client for interacting with Cloudflare R2 cloud storage using cloudpathlib."""

    def __init__(
        self,
        bucket_name: str,
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
    ):
        """Initialize CloudStorageClient with cloudpathlib."""
        self.access_key = access_key or os.getenv("BUCKET_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("BUCKET_SECRET_ACCESS_KEY")
        self.endpoint_url = endpoint_url or os.getenv("BUCKET_ENDPOINT_URL")
        self.bucket_name = bucket_name

        if not all(
            [self.access_key, self.secret_key, self.endpoint_url, self.bucket_name],
        ):
            raise OSError("Missing required credentials or bucket information.")

        self.client = S3Client(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url,
        )

        self.bucket = S3Path(f"{self.bucket_name}", client=self.client)

    def download_file(
        self,
        object_key: str,
        destination_name: str | Path,
    ) -> Path:
        """Read the content of an object from Cloudflare R2 bucket saves it to destination_name.

        Args:
            object_key (str): The key of the object to download from the bucket.
            destination_name (Union[str, Path]): The name of the file where the content will be saved.

        Returns:
            Path: The path to the downloaded and renamed file.
        """
        file_path = self.bucket / object_key
        destination_name = (
            Path(destination_name)
            if isinstance(destination_name, str)
            else destination_name
        )
        if not destination_name.exists():
            open(destination_name, "w+", encoding="utf-8").close()
        return file_path.download_to(destination=destination_name)

    def upload_file(
        self,
        local_file_path: str | Path,
        object_key: str | None = None,
    ) -> str:
        """Uploads a file to a Cloudflare R2 bucket."""
        if object_key is None:
            object_key = str(uuid.uuid1())

        file_path = self.bucket / object_key
        file_path.upload_from(source=local_file_path)
        return object_key


if __name__ == "__main__":
    import tempfile

    BUCKET_NAME = "s3://structures"
    storage_client = CloudStorageClient(bucket_name=BUCKET_NAME)
    try:
        fn_in = "README.md"
        object_key = storage_client.upload_file(fn_in)
        print(
            f"File {fn_in} uploaded successfully as {object_key} in {BUCKET_NAME} bucket",
        )
        # Create a temporary file and close it to avoid locking issues on Windows
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file_path = temp_file.name
        temp_file.close()

        # Download the file to the temporary file path
        downloaded_path = storage_client.download_file(
            object_key=object_key,
            destination_name=temp_file_path,
        )
        print(f"File downloaded to temporary file: {downloaded_path}")
    except Exception as e:
        print(f"Error: {e}")
