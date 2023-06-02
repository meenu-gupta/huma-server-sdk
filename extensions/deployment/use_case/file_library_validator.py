from abc import ABC, abstractmethod
import os

from extensions.deployment.use_case.file_library_metadata import (
    MetadataFields,
    LibraryType,
)
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    InternalServerErrorException,
)
from sdk.storage.model.file_storage import FileStorage


class FileLibraryValidator(ABC):
    @staticmethod
    @abstractmethod
    def validate_file(file: FileStorage):
        raise NotImplementedError


class HumaImageLibraryValidator(FileLibraryValidator):
    SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".tiff", ".png"]

    @staticmethod
    def validate_file(file: FileStorage):
        content_type = file.contentType or ""
        if not content_type.startswith("image/"):
            msg = f"File with id #{file.id} and contentType {content_type} is not an image file"
            raise InvalidRequestException(msg)
        file_name = file.fileName or ""
        _, file_extension = os.path.splitext(file_name)
        if file_extension.lower() not in HumaImageLibraryValidator.SUPPORTED_EXTENSIONS:
            msg = f"Extension {file_extension} is not supported. File id: {file.id}"
            raise InvalidRequestException(msg)


class OptionsLibraryValidator(FileLibraryValidator):
    MAX_FILE_SIZE = 2048 * 1024
    MAX_OPTIONS_COUNT = 500
    SUPPORTED_EXTENSIONS = [".csv", ".xlsx"]

    @staticmethod
    def validate_file(file: FileStorage):
        if file.fileSize > OptionsLibraryValidator.MAX_FILE_SIZE:
            file_size_in_mb = OptionsLibraryValidator.MAX_FILE_SIZE / 1024 / 1024
            msg = f"File size exceeds {int(file_size_in_mb)} MB"
            raise InvalidRequestException(msg)

        _, file_extension = os.path.splitext(file.fileName)
        if file_extension.lower() not in OptionsLibraryValidator.SUPPORTED_EXTENSIONS:
            msg = f"Extension {file_extension} is not supported. File id: {file.id}"
            raise InvalidRequestException(msg)

        if MetadataFields.LIST_COUNT not in file.metadata:
            msg = f"Metadata field {MetadataFields.LIST_COUNT} is not present for file id {file.id}"
            raise InternalServerErrorException(msg)

        list_size = file.metadata[MetadataFields.LIST_COUNT]
        if not list_size:
            msg = f"Metadata field {MetadataFields.LIST_COUNT} is not set for file id {file.id}"
            raise InvalidRequestException(msg)
        if list_size > OptionsLibraryValidator.MAX_OPTIONS_COUNT:
            msg = (
                f"Metadata field {MetadataFields.LIST_COUNT} is "
                f"greater than {OptionsLibraryValidator.MAX_OPTIONS_COUNT} "
                f"for file id {file.id}"
            )
            raise InvalidRequestException(msg)


class HumaOptionsLibraryValidator(OptionsLibraryValidator):
    pass


class DeploymentOptionsLibraryValidator(OptionsLibraryValidator):
    pass


class FileLibraryValidatorFactory:
    library_validators = {
        LibraryType.HUMA_IMAGE_LIBRARY.value: HumaImageLibraryValidator,
        LibraryType.HUMA_OPTIONS_LIBRARY.value: HumaOptionsLibraryValidator,
        LibraryType.DEPLOYMENT_OPTIONS_LIBRARY.value: DeploymentOptionsLibraryValidator,
    }

    @staticmethod
    def get_validator(libraryId: str) -> FileLibraryValidator:
        return FileLibraryValidatorFactory.library_validators.get(libraryId)
