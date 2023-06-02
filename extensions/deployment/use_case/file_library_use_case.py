from flask import g

from extensions.deployment.use_case.file_library_validator import (
    FileLibraryValidatorFactory,
)
from sdk.common.exceptions.exceptions import (
    FileNotFoundException,
    InvalidRequestException,
    PermissionDenied,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values
from sdk.storage.model.file_storage import FileStorage
from sdk.storage.repository.storage_repository import StorageRepository

from extensions.deployment.use_case.file_library_metadata import (
    STANDARD_LIBRARIES,
    FileLibraryMetadataFactory,
)
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.router.deployment_requests import (
    AddFilesToLibraryRequestObject,
    LibraryFileObject,
    RetrieveFilesInLibraryRequestObject,
    RetrieveFilesInLibraryResponseObject,
)
from extensions.deployment.use_case.file_library_validator import LibraryType


class FileLibraryUseCase(UseCase):
    @autoparams()
    def __init__(
        self, storage_repo: StorageRepository, deployment_repo: DeploymentRepository
    ):
        self._storage_repo = storage_repo
        self._deployment_repo = deployment_repo
        self._metadata_factory = FileLibraryMetadataFactory
        self._validator_factory = FileLibraryValidatorFactory


class AddFilesToLibraryUseCase(FileLibraryUseCase):
    request_object: AddFilesToLibraryRequestObject

    def process_request(self, request_object: AddFilesToLibraryRequestObject):
        self.request_object = request_object
        library_id = request_object.libraryId
        if library_id not in list(map(lambda x: x.value, LibraryType)):
            raise InvalidRequestException(f"Invalid libraryId: {library_id}")

        self._check_library_permission(library_id)

        for file_id in request_object.fileIds:
            if not self._storage_repo.file_exists(file_id=file_id):
                raise FileNotFoundException

        files = self._storage_repo.get_files(file_ids=request_object.fileIds)
        if self._needs_metadata_creation():
            self._create_metadata(files=files)
            self._validate_files(files=files)
            self._store_with_metadata(files=files)
        else:
            self._validate_files(files=files)
            self._store_with_metadata()

    @staticmethod
    def _check_library_permission(library_id: str):
        is_huma_library = library_id in STANDARD_LIBRARIES
        is_user_super_admin = g.authz_user and g.authz_user.is_super_admin()
        if is_huma_library and not is_user_super_admin:
            raise PermissionDenied

    def _validate_files(self, files: list[FileStorage]):
        validator = self._validator_factory.get_validator(self.request_object.libraryId)
        if validator:
            for file in files:
                validator.validate_file(file)

    def _needs_metadata_creation(self):
        return (
            self._metadata_factory.get_metadata_creator(self.request_object.libraryId)
            is not None
        )

    def _create_metadata(self, files: list[FileStorage]):
        metadata = self._shared_metadata()
        metadata_creator = self._metadata_factory.get_metadata_creator(
            self.request_object.libraryId
        )
        for file in files:
            library_metadata = metadata_creator.create_metadata(file)
            file.metadata = remove_none_values(metadata | library_metadata)

    def _store_with_metadata(self, files: list[FileStorage] = None):
        if files:
            for file in files:
                self._storage_repo.update_metadata(
                    file_id=file.id,
                    metadata=file.metadata,
                )
        else:
            metadata = self._shared_metadata()
            self._storage_repo.update_multiple_files_metadata(
                file_ids=self.request_object.fileIds,
                metadata=remove_none_values(metadata),
            )

    def _shared_metadata(self):
        return {
            AddFilesToLibraryRequestObject.LIBRARY_ID: self.request_object.libraryId,
            AddFilesToLibraryRequestObject.DEPLOYMENT_ID: self.request_object.deploymentId,
        }


class RetrieveFilesInLibraryUseCase(FileLibraryUseCase):
    def process_request(self, request_object: RetrieveFilesInLibraryRequestObject):
        is_deployment_library = request_object.libraryId not in STANDARD_LIBRARIES
        deployment_id = request_object.deploymentId if is_deployment_library else None
        files = self._deployment_repo.retrieve_files_in_library(
            library_id=request_object.libraryId,
            deployment_id=deployment_id,
            offset=request_object.offset,
            limit=request_object.limit,
        )
        response_files = [LibraryFileObject.from_dict(file.to_dict()) for file in files]
        response = {RetrieveFilesInLibraryResponseObject.FILES: response_files}
        return response
