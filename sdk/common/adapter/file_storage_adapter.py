import abc
from abc import ABC
from io import BytesIO
from typing import BinaryIO


class FileStorageAdapter(ABC):
    """Abstract storage adapter"""

    APP_OCTET_STREAM = "application/octet-stream"

    @abc.abstractmethod
    def copy(self, object_name: str, new_object_name: str, bucket_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        data_size: int = 0,
        file_type: str = APP_OCTET_STREAM,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def download_file(
        self, bucket_name: str, object_name: str
    ) -> tuple[BytesIO, int, str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_pre_signed_url(self, bucket_name: str, object_name: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def file_exist(self, bucket_name: str, object_name: str) -> bool:
        raise NotImplementedError

    def delete_folder(self, bucket_name: str, folder_name: str) -> int:
        raise NotImplementedError
