import logging
from io import BytesIO
from typing import BinaryIO

from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError

from sdk.common.adapter.file_storage_adapter import FileStorageAdapter

_SIGNED_URL_LIFE = 7  # day in unit
logger = logging.getLogger(__name__)


class TencentCosFileStorageAdapter(FileStorageAdapter):
    def __init__(self, cos_config: CosConfig):
        self._client = CosS3Client(cos_config, retry=3)

    def copy(self, object_name: str, new_object_name: str, bucket_name: str):
        return self._client.copy_object(bucket_name, new_object_name, object_name)

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        data_size: int = 0,
        file_type: str = "application/octet-stream",
    ) -> None:
        """
        adapter.upload_file(bucket_name=bucket, object_name="test1/bun.mp4", data=content)
        # NOTE the content argument can be file-like object
        """
        self._client.put_object(
            bucket_name, data, object_name, StorageClass="STANDARD", EnableMD5=False
        )

    def download_file(
        self, bucket_name: str, object_name: str
    ) -> tuple[BytesIO, int, str]:
        """
        content, content_length, content_type = adapter.download_file("bucket1", "test1/bun.mp4")
        """
        cos_rsp = self._client.get_object(Bucket=bucket_name, Key=object_name)
        return (
            BytesIO(cos_rsp["Body"].get_raw_stream().data),
            cos_rsp.get("Content-Length"),
            cos_rsp.get("Content-Type") or "application/octet-stream",
        )

    def generate_signed_url(
        self, base_url, bucket_name, object_name, access_key, secret_key
    ):
        raise NotImplementedError

    def get_pre_signed_url(self, bucket_name: str, object_name: str) -> str:
        """
        url = adapter.get_pre_signed_url("bucket1", "test1/bun.mp4")
        """
        return self._client.get_presigned_download_url(
            Bucket=bucket_name, Key=object_name, Expired=_SIGNED_URL_LIFE * 24 * 3600
        )

    def file_exist(self, bucket_name: str, object_name: str) -> bool:
        try:
            return self._client.object_exists(Bucket=bucket_name, Key=object_name)

        except CosServiceError as e:
            logger.error(
                f"CosServiceError details: {e.get_status_code()} / {e.get_digest_msg()}"
            )
            raise e
