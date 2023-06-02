import datetime
import logging
from io import BytesIO
from typing import BinaryIO

from azure.storage.blob import (
    ContainerClient,
    ContentSettings,
    generate_blob_sas,
    BlobSasPermissions,
    BlobClient,
)
from azure.storage.blob._shared.base_client import parse_connection_str

from sdk.common.adapter.azure.azure_blob_storage_config import AzureBlobStorageConfig
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter

logger = logging.getLogger(__name__)


def get_blob_sas(account_name, account_key, container_name, blob_name):
    sas_blob = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(days=7),
    )
    return sas_blob


def get_url(account_name, account_key, container_name, blob_name):
    blob = get_blob_sas(account_name, account_key, container_name, blob_name)
    return (
        "https://"
        + account_name
        + ".blob.core.windows.net/"
        + container_name
        + "/"
        + blob_name
        + "?"
        + blob
    )


class AzureBlobStorageAdapter(FileStorageAdapter):
    """
    how to configure it:
    > azureBlobStorageConfig:
    >   connectionString: !ENV ${MP_AZURE_BLOB_STORAGE_CONN_STR}

    how to use it:
    > adapter: AzureBlobStorageAdapter = inject.instance('azureBlobStorageAdapter')
    > blob_result = adapter.download_file("hu-pp-pre", "user/user_id/test.png")
    """

    def __init__(self, config: AzureBlobStorageConfig):
        self._conn_str = config.connectionString

    def copy(self, object_name: str, new_object_name: str, bucket_name: str):
        file, _, _ = self.download_file(bucket_name, object_name)
        return self.upload_file(bucket_name, new_object_name, file)

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        data_size: int = 0,
        file_type: str = "application/octet-stream",
    ) -> None:
        container_client = ContainerClient.from_connection_string(
            self._conn_str, container_name=bucket_name
        )
        container_client.upload_blob(
            name=object_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=file_type),
        )

    def download_file(self, bucket_name: str, object_name: str) -> (BytesIO, int, str):
        blob_client = BlobClient.from_connection_string(
            self._conn_str, container_name=bucket_name, blob_name=object_name
        )
        blob_data = blob_client.download_blob().readall()

        return (
            BytesIO(blob_data),
            len(blob_data),
            blob_client.get_blob_properties().content_settings.content_type
            or "application/octet-stream",
        )

    def get_pre_signed_url(self, bucket_name: str, object_name: str) -> str:
        account_url, secondary, credential = parse_connection_str(
            self._conn_str, None, "blob"
        )
        return get_url(
            credential["account_name"],
            credential["account_key"],
            bucket_name,
            object_name,
        )

    def file_exist(self, bucket_name: str, object_name: str) -> bool:
        return BlobClient.from_connection_string(
            conn_str=self._conn_str, container_name=bucket_name, blob_name=object_name
        ).exists()
