from bson import ObjectId
from pymongo import WriteConcern, MongoClient

from sdk.common.exceptions.exceptions import (
    FileNotFoundException,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.storage.model.file_storage import FileStorage
from sdk.storage.repository.storage_repository import StorageRepository


class MongoStorageRepository(StorageRepository):
    STORAGE_COLLECTION = "filestorage"

    @autoparams()
    def __init__(self, client: MongoClient):
        self._config = inject.instance(PhoenixServerConfig)
        self._database = self._config.server.adapters.mongodbDatabase.name
        self._client = client
        self._db = client.get_database(
            self._database, write_concern=WriteConcern("majority", wtimeout=10000)
        )

    def add_file(self, file: FileStorage) -> str:
        return str(
            self._db[self.STORAGE_COLLECTION]
            .insert_one(remove_none_values(file.to_dict()))
            .inserted_id
        )

    def get_file(self, file_id: str) -> FileStorage:
        query = {FileStorage.ID_: ObjectId(file_id)}
        result = self._db[self.STORAGE_COLLECTION].find_one(query)
        if result is None:
            raise FileNotFoundException
        file = FileStorage.from_dict(result)
        file.id = str(result[FileStorage.ID_])
        return file

    def get_files(self, file_ids: list[str]) -> list[FileStorage]:
        query = {
            FileStorage.ID_: {"$in": [ObjectId(file_id) for file_id in set(file_ids)]}
        }
        results = self._db[self.STORAGE_COLLECTION].find(query)
        files = []
        for result in results:
            file = FileStorage.from_dict(result)
            file.id = str(result[FileStorage.ID_])
            files.append(file)
        return files

    def set_file_key(self, file_id: str, key: str):
        match_query = {FileStorage.ID_: ObjectId(file_id)}
        update_query = {"$set": {FileStorage.KEY: key}}
        self._db[self.STORAGE_COLLECTION].update_one(match_query, update_query)

    def file_exists(self, file_id: str):
        query = {
            FileStorage.ID_: ObjectId(file_id),
            FileStorage.KEY: {"$exists": True, "$ne": None},
        }
        results = self._db[self.STORAGE_COLLECTION].find(query)
        return results.count() > 0

    def remove_file(self, file_id: str):
        query = {FileStorage.ID_: ObjectId(file_id)}
        self._db[self.STORAGE_COLLECTION].delete_one(query)

    def update_metadata(self, file_id: str, metadata: dict):
        match_query = {FileStorage.ID_: ObjectId(file_id)}
        update_query = {"$set": {FileStorage.METADATA: metadata}}
        self._db[self.STORAGE_COLLECTION].update_one(match_query, update_query)

    def update_multiple_files_metadata(self, file_ids: list[str], metadata: dict):
        match_query = {
            FileStorage.ID_: {"$in": [ObjectId(file_id) for file_id in set(file_ids)]}
        }
        update_query = {"$set": {FileStorage.METADATA: metadata}}
        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                self._db[self.STORAGE_COLLECTION].update_many(match_query, update_query)

    def create_indexes(self):
        self._db[self.STORAGE_COLLECTION].ensure_index(
            FileStorage.KEY, unique=True, sparse=True
        )
        self._db[self.STORAGE_COLLECTION].ensure_index(FileStorage.USER_ID)
