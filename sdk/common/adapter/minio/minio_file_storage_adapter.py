import logging
import urllib.parse
from datetime import timedelta
from io import BytesIO
from typing import BinaryIO

from minio import Minio
from minio.credentials import Credentials, Chain, Static
from minio.error import NoSuchKey, NoSuchBucket
from minio.helpers import is_non_empty_string, get_target_url
from minio.signer import presign_v4

from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.adapter.minio.minio_config import MinioConfig

_SIGNED_URL_LIFE = 7  # day in unit
logger = logging.getLogger(__name__)


class MinioFileStorageAdapter(FileStorageAdapter):
    def __init__(self, config: MinioConfig):
        self._config = config
        self._client = Minio(
            self._config.url,
            self._config.accessKey,
            self._config.secretKey,
            secure=self._config.secure,
        )
        self._base_url = self._config.baseUrl
        self._service_url = self._config.serviceUrl

    def copy(self, object_name: str, new_object_name: str, bucket_name: str):
        source = f"{bucket_name}/{object_name}"
        return self._client.copy_object(bucket_name, new_object_name, source)

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        data_size: int = 0,
        file_type: str = "application/octet-stream",
    ) -> None:
        self._client.put_object(
            bucket_name, object_name, data, data_size, content_type=file_type
        )

    def download_file(
        self, bucket_name: str, object_name: str
    ) -> tuple[BytesIO, int, str]:
        http_rsp = self._client.get_object(
            bucket_name=bucket_name, object_name=object_name
        )
        return (
            BytesIO(http_rsp.data),
            len(http_rsp.data),
            http_rsp.headers.get("Content-Type") or "application/octet-stream",
        )

    def generate_signed_url(
        self, base_url, bucket_name, object_name, access_key, secret_key
    ):
        is_non_empty_string(object_name)
        region = "us-east-1"
        url = get_target_url(
            base_url,
            bucket_name=bucket_name,
            object_name=object_name,
            bucket_region=region,
        )
        cred = Credentials(provider=Chain(providers=[Static(access_key, secret_key)]))
        return presign_v4(
            "GET",
            url,
            cred,
            secret_key,
            expires=int(timedelta(days=_SIGNED_URL_LIFE).total_seconds()),
        )

    def get_pre_signed_url(self, bucket_name: str, object_name: str) -> str:
        if not self._base_url:
            return self._client.presigned_get_object(
                bucket_name, object_name, timedelta(days=7)
            )

        url = self.generate_signed_url(
            self._base_url,
            bucket_name,
            object_name,
            self._config.accessKey,
            self._config.secretKey,
        )
        parsed_url = urllib.parse.urlparse(url)
        parsed_base_url = urllib.parse.urlparse(self._base_url)
        final_url = parsed_url._replace(
            netloc=parsed_base_url.netloc, scheme=parsed_base_url.scheme
        ).geturl()
        if self._service_url:
            new_path = self._service_url + parsed_url.path
            final_url = parsed_url._replace(
                netloc=parsed_base_url.netloc,
                scheme=parsed_base_url.scheme,
                path=new_path,
            ).geturl()
        return final_url

    def file_exist(self, bucket_name: str, object_name: str) -> bool:
        try:
            metadata = self._client.stat_object(
                bucket_name=bucket_name, object_name=object_name
            )
            return metadata is not None

        except NoSuchKey:
            return False

        except NoSuchBucket:
            return False
