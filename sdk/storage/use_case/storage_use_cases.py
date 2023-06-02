import datetime
import io
import os


# debugging value _EXPIRATION_DELTA_VALUE = datetime.timedelta(seconds=2)
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import (
    BucketFileDoesNotExist,
    InvalidRequestException,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import (
    PhoenixServerConfig,
    StorageConfig,
    StorageAdapter,
)
from sdk.storage.model.file_storage import FileStorage
from sdk.storage.repository.storage_repository import StorageRepository
from sdk.storage.use_case.storage_request_objects import (
    DownloadFileRequestObjectV1,
    GetSignedUrlRequestObjectV1,
    UploadFileRequestObject,
    DownloadFileRequestObject,
    GetSignedUrlRequestObject,
    UploadFileRequestObjectV1,
)
from sdk.storage.use_case.storage_response_objects import (
    DownloadFileResponseObject,
    DownloadFileResponseObjectV1,
    GetSignedUrlResponseObject,
    GetSignedUrlResponseObjectV1,
    UploadFileResponseObjectV1,
)

_EXPIRATION_DELTA_VALUE = datetime.timedelta(days=1)


def get_file_adapter(config: StorageConfig) -> FileStorageAdapter:
    if config.storageAdapter == StorageAdapter.MINIO:
        return inject.instance("minioFileStorage")
    elif config.storageAdapter == StorageAdapter.OSS:
        return inject.instance("ossFileStorage")
    elif config.storageAdapter == StorageAdapter.GCS:
        return inject.instance("gcsFileStorage")
    elif config.storageAdapter == StorageAdapter.AZURE:
        return inject.instance("azureFileStorage")
    raise RuntimeError("Adapter for FileStorage not set")


class StorageUseCase(UseCase):
    @autoparams()
    def __init__(self, config: PhoenixServerConfig):
        self._file_adapter = get_file_adapter(config.server.storage)


class UploadFileUseCase(StorageUseCase):
    def process_request(self, request_object: UploadFileRequestObject):
        value_as_a_stream = io.BytesIO(request_object.fileData)  # io.BytesIO
        self._file_adapter.upload_file(
            request_object.bucket,
            request_object.filename,
            value_as_a_stream,
            len(request_object.fileData),
            file_type=request_object.mime
            if request_object.mime is not None
            else self._file_adapter.APP_OCTET_STREAM,
        )


class DownloadFileUseCase(StorageUseCase):
    def process_request(self, request_object: DownloadFileRequestObject):
        if not self._file_adapter.file_exist(
            request_object.bucket, request_object.filename
        ):
            raise BucketFileDoesNotExist
        content, content_length, content_type = self._file_adapter.download_file(
            request_object.bucket, request_object.filename
        )
        return DownloadFileResponseObject(content, content_length, content_type)


class GetSignedUrlUseCase(StorageUseCase):
    def process_request(self, request_object: GetSignedUrlRequestObject):
        if not self._file_adapter.file_exist(
            request_object.bucket, request_object.filename
        ):
            raise BucketFileDoesNotExist

        signed_url = self._get_pre_signed_url(
            request_object.bucket, request_object.filename
        )
        return GetSignedUrlResponseObject(url=signed_url)

    def _get_pre_signed_url(self, bucket: str, filename: str) -> str:
        try:
            signed_url = self._file_adapter.get_pre_signed_url(bucket, filename)
        except Exception:
            # as different file adapter getting url in a different way,
            # we are trying to catch any possible exception
            raise InvalidRequestException("Error while getting pre-signed url")
        else:
            return signed_url


class StorageUseCaseV1(UseCase):
    @autoparams()
    def __init__(self, config: PhoenixServerConfig, repo: StorageRepository):
        self._bucket_name = config.server.storage.defaultBucket
        self._repo = repo
        self._file_adapter = get_file_adapter(config.server.storage)


class UploadFileUseCaseV1(StorageUseCaseV1):
    def process_request(self, request_object: UploadFileRequestObjectV1):
        user_id = request_object.userId
        file = FileStorage.from_dict(
            {
                FileStorage.FILE_NAME: request_object.fileName,
                FileStorage.FILE_SIZE: request_object.fileSize,
                FileStorage.CONTENT_TYPE: request_object.contentType,
                FileStorage.CREATED_AT: datetime.datetime.utcnow(),
                FileStorage.USER_ID: user_id,
            }
        )
        file_id = self._repo.add_file(file)
        file_extension = os.path.splitext(request_object.fileName)[1]
        key = f"files/user/{user_id}/{file_id}{file_extension}"
        self._file_adapter.upload_file(
            bucket_name=self._bucket_name,
            object_name=key,
            data=io.BytesIO(request_object.fileData),
            data_size=request_object.fileSize,
            file_type=request_object.contentType or self._file_adapter.APP_OCTET_STREAM,
        )
        self._repo.set_file_key(file_id=file_id, key=key)
        return UploadFileResponseObjectV1(id=file_id)


class DownloadFileUseCaseV1(StorageUseCaseV1):
    def process_request(self, request_object: DownloadFileRequestObjectV1):
        file = self._repo.get_file(request_object.fileId)
        if not self._file_adapter.file_exist(self._bucket_name, file.key):
            raise BucketFileDoesNotExist
        content, content_length, content_type = self._file_adapter.download_file(
            self._bucket_name, file.key
        )
        return DownloadFileResponseObjectV1(
            file.fileName, content, content_length, content_type
        )


class GetSignedUrlUseCaseV1(StorageUseCaseV1):
    def process_request(self, request_object: GetSignedUrlRequestObjectV1):
        file = self._repo.get_file(request_object.fileId)
        if not self._file_adapter.file_exist(self._bucket_name, file.key):
            raise BucketFileDoesNotExist

        signed_url = self._get_pre_signed_url(self._bucket_name, file.key)
        return GetSignedUrlResponseObjectV1(
            url=signed_url,
            file_name=file.fileName,
            file_size=file.fileSize,
            content_type=file.contentType,
        )

    def _get_pre_signed_url(self, bucket: str, filename: str) -> str:
        try:
            signed_url = self._file_adapter.get_pre_signed_url(bucket, filename)
        except Exception:
            raise InvalidRequestException("Error while getting pre-signed url")
        else:
            return signed_url
