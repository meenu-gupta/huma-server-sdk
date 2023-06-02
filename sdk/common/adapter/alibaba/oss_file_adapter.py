import logging
from datetime import timedelta
from io import BytesIO
from typing import BinaryIO

import oss2
from minio.helpers import is_non_empty_string, is_valid_bucket_name, get_target_url
from minio.signer import presign_v4

from sdk.common.adapter.alibaba.oss_config import OSSConfig
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils.inject import autoparams

_SIGNED_URL_LIFE = 7 * 24 * 3600  # day in unit
logger = logging.getLogger(__name__)


class OSSFileStorageAdapter(FileStorageAdapter):
    @autoparams()
    def __init__(self, config: OSSConfig):
        self._config = config

    @property
    def auth(self):
        return oss2.Auth(self._config.accessKeyId, self._config.accessKeySecret)

    def copy(self, object_name: str, new_object_name: str, bucket_name: str):
        bucket = oss2.Bucket(self.auth, self._config.url, bucket_name)
        bucket.copy_object(bucket_name, object_name, new_object_name)

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        data_size: int = 0,
        file_type: str = "application/octet-stream",
    ) -> None:
        bucket = oss2.Bucket(self.auth, self._config.url, bucket_name)
        bucket.put_object(object_name, data, headers={"Content-Type": file_type})

    def download_file(
        self, bucket_name: str, object_name: str
    ) -> tuple[BytesIO, int, str]:
        bucket = oss2.Bucket(self.auth, self._config.url, bucket_name)
        rsp = bucket.get_object(object_name)
        return (
            BytesIO(rsp.read()),
            rsp.content_length,
            rsp.headers.get("Content-Type") or "application/octet-stream",
        )

    def generate_signed_url(
        self, base_url, bucket_name, object_name, access_key, secret_key
    ):
        is_valid_bucket_name(bucket_name)
        is_non_empty_string(object_name)
        region = "us-east-1"
        url = get_target_url(
            base_url,
            bucket_name=bucket_name,
            object_name=object_name,
            bucket_region=region,
        )
        return presign_v4(
            "GET",
            url,
            access_key,
            secret_key,
            expires=int(timedelta(days=_SIGNED_URL_LIFE).total_seconds()),
        )

    def get_pre_signed_url(self, bucket_name: str, object_name: str) -> str:
        auth = oss2.Auth(self._config.accessKeyId, self._config.accessKeySecret)
        bucket = oss2.Bucket(auth, self._config.url, bucket_name)
        return bucket.sign_url("GET", object_name, _SIGNED_URL_LIFE)

    def file_exist(self, bucket_name: str, object_name: str) -> bool:
        auth = oss2.Auth(self._config.accessKeyId, self._config.accessKeySecret)
        bucket = oss2.Bucket(auth, self._config.url, bucket_name)
        return bucket.object_exists(key=object_name)
