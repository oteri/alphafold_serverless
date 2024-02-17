"""Manages the low level interfaces with cloudflare."""
import os
from pathlib import Path
from typing import Union
import uuid
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv(verbose=True)


class CloudStorageClient:
    """A client for interacting with Cloudflare R2 cloud storage.

    This class encapsulates methods to upload and download files to and from
    Cloudflare R2 buckets. It can be initialized with specific credentials
    and endpoint URL or use credentials obtained from environment variables.

    Attributes:
        access_key (str): Access key ID for Cloudflare R2.
        secret_key (str): Secret access key for Cloudflare R2.
        endpoint_url (str): Endpoint URL for Cloudflare R2.
        s3 (boto3.client): Boto3 S3 client instance.

    Raises:
        NoCredentialsError: If R2 credentials are missing or invalid.
    """

    def __init__(
        self,
        access_key: Union[str, None] = None,
        secret_key: Union[str, None] = None,
        endpoint_url: Union[str, None] = None,
        bucket_name: Union[str, None] = None,
    ):
        """Initialize CloudStorageClient.

        Args:
            access_key (Union[str, None], optional): Access key. Defaults to None.
            secret_key (Union[str, None], optional): secret key. Defaults to None.
            endpoint_url (Union[str, None], optional): endpoint url. Defaults to None.
            bucket_name (Union[str, None], optional): bucket name. Defaults to None.

        Raises:
            NoCredentialsError: _description_
        """
        self.access_key = access_key or os.getenv("BUCKET_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("BUCKET_SECRET_ACCESS_KEY")
        self.endpoint_url = endpoint_url or os.getenv("BUCKET_ENDPOINT_URL")
        self.bucket_name = bucket_name or os.environ["BUCKET_NAME"]

        if not self.access_key or not self.secret_key or not self.endpoint_url:
            raise NoCredentialsError()

        self.session = boto3.session.Session()
        self.s3 = self.session.client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def download_file(
        self, object_key: str, destination_path: Union[str, Path]
    ) -> None:
        """Downloads a file from a Cloudflare R2 bucket.

        Args:
            object_key (str): The object key (i.e., file name) in the bucket.
            destination_path (Union[str, Path]): The local file system path where the file will be downloaded.
        """
        self.s3.download_file(self.bucket_name, object_key, str(destination_path))
        print(f"File {object_key} downloaded successfully to {destination_path}")

    def upload_file(
        self, local_file_path: Union[str, Path], object_key: Union[str, None] = None
    ) -> str:
        """Uploads a file to a Cloudflare R2 bucket.

        Args:
            local_file_path (Union[str, Path]): The local file system path of the file to be uploaded.
            object_key (str): The object key (i.e., file name) under which the file will be stored in the bucket.
                                If None, a unique name is generated.

        Returns:
            str: the name of the object 'either the one supplied or the one generated)
        """
        if object_key is None:
            object_key = str(uuid.uuid1())
        self.s3.upload_file(str(local_file_path), self.bucket_name, object_key)
        print(
            f"File {local_file_path} uploaded successfully as {object_key} in {self.bucket_name} bucket"
        )
        return object_key


# Example usage
if __name__ == "__main__":
    file_extension = ".txt"
    object_name = f"{uuid.uuid4()}{file_extension}"
    storage_client = CloudStorageClient()
    try:
        object_key = storage_client.upload_file("README.md")
        storage_client.download_file(object_key=object_key, destination_path=object_key)
    except NoCredentialsError as e:
        print(f"Error: {e}")
