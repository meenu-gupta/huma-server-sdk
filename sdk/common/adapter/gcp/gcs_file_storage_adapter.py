import datetime
import logging
import os
from io import BytesIO
from typing import BinaryIO

from google.cloud import storage
from google.cloud.storage import Bucket, Blob

from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.adapter.gcp.gcs_config import GCSConfig
from sdk.common.exceptions.exceptions import BucketFileDoesNotExist

logger = logging.getLogger(__name__)


class GCSFileStorageAdapter(FileStorageAdapter):
    """
    how to configure it:
    > gcsConfig:
    >   serviceAccountKeyFilePath: !ENV ${MP_GCS_SA_FILE_PATH}

    how to use it:
    > adapter: GCSFileStorageAdapter = inject.instance('gcsFileStorageAdapter')
    > blob_result = adapter.download_file("hu-pp-pre", "user/user_id/test.png")
    """

    def __init__(self, config: GCSConfig):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.serviceAccountKeyFilePath
        self.client = storage.Client()
        self.buckets: dict[str, Bucket] = dict()

    def copy(self, object_name: str, new_object_name: str, bucket_name: str):
        bucket: Bucket = self.client.bucket(bucket_name)
        object_blob = bucket.blob(object_name)
        bucket.copy_blob(object_blob, bucket, new_object_name)

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        data_size: int = 0,
        file_type: str = "application/octet-stream",
    ) -> None:

        bucket: Bucket = self.client.bucket(bucket_name)
        object_blob = bucket.blob(object_name)
        return object_blob.upload_from_file(
            file_obj=data, content_type=file_type, size=data_size
        )

    def download_file(
        self, bucket_name: str, object_name: str
    ) -> tuple[BytesIO, int, str]:
        bucket: Bucket = self._get_bucket(bucket_name)
        object_blob = self._get_object_from_bucket_or_raise_error(bucket, object_name)
        file_content = object_blob.download_as_string()
        return BytesIO(file_content), len(file_content), object_blob.content_type

    def _get_bucket(self, bucket_name: str) -> Bucket:
        bucket = self.buckets.get(bucket_name)
        if not bucket:
            bucket = self.client.bucket(bucket_name)
            self.buckets[bucket_name] = bucket
        return bucket

    @staticmethod
    def _get_object_from_bucket_or_raise_error(
        bucket: Bucket, object_name: str
    ) -> Blob:
        if object_blob := bucket.get_blob(object_name):
            return object_blob
        raise BucketFileDoesNotExist

    def get_pre_signed_url(self, bucket_name: str, object_name: str) -> str:
        bucket: Bucket = self.client.bucket(bucket_name)
        object_blob = self._get_object_from_bucket_or_raise_error(bucket, object_name)
        return object_blob.generate_signed_url(expiration=datetime.timedelta(days=7))

    def file_exist(self, bucket_name: str, object_name: str) -> bool:
        bucket: Bucket = self.client.bucket(bucket_name)
        return bucket.blob(object_name).exists()

    def delete_folder(self, bucket_name: str, folder_name: str) -> tuple[int, int]:
        bucket: Bucket = self.client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=folder_name)
        number_of_deleted_successfully = 0
        number_of_blobs = 0
        for blob in blobs:
            try:
                blob.delete()
                number_of_deleted_successfully += 1
            except Exception as e:
                logger.warning(e)
            number_of_blobs += 1

        return number_of_blobs, number_of_deleted_successfully
