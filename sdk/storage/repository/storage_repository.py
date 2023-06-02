import abc
from abc import ABC

from sdk.storage.model.file_storage import FileStorage


class StorageRepository(ABC):
    session = None

    @abc.abstractmethod
    def add_file(self, file: FileStorage) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_file(self, file_id: str) -> FileStorage:
        raise NotImplementedError

    @abc.abstractmethod
    def get_files(self, file_ids: list[str]) -> list[FileStorage]:
        raise NotImplementedError

    @abc.abstractmethod
    def set_file_key(self, file_id: str, key: str):
        raise NotImplementedError

    @abc.abstractmethod
    def file_exists(self, file_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_file(self, file_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def update_metadata(self, file_id: str, metadata: dict):
        raise NotImplementedError

    @abc.abstractmethod
    def update_multiple_files_metadata(self, file_ids: list[str], metadata: dict):
        raise NotImplementedError

    @abc.abstractmethod
    def create_indexes(self):
        raise NotImplementedError
