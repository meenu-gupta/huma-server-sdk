from typing import Any

from werkzeug.utils import secure_filename

from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    not_empty,
    validate_object_id,
    must_be_at_least_one_of,
)


@convertibleclass
class StorageRequestObject(RequestObject):
    BUCKET = "bucket"
    FILENAME = "filename"
    bucket: str = required_field(metadata=meta(not_empty))
    filename: str = required_field()


@convertibleclass
class UploadFileRequestObject(RequestObject):
    MIME = "mime"
    FILE = "file"
    FILE_DATA = "fileData"
    FILENAME = "filename"
    BUCKET = "bucket"
    mime: str = default_field()
    fileData: Any = default_field()
    file: Any = default_field()
    filename: str = default_field()
    bucket: str = required_field(metadata=meta(not_empty))

    def validate(self):
        must_be_at_least_one_of(
            file=self.file, file_name_and_data=self.filename and self.fileData
        )

    def post_init(self):
        if not self.fileData:
            self.fileData = self.file.read()
        if not self.filename:
            self.filename = self.file.name or self.file.filename


@convertibleclass
class DownloadFileRequestObject(StorageRequestObject):
    pass


@convertibleclass
class GetSignedUrlRequestObject(StorageRequestObject):
    HOST = "host"
    host: str = required_field()


@convertibleclass
class DownloadSignedUrlRequestObject(RequestObject):
    ENCODED_OBJECT = "encodedObject"
    encodedObject: str = required_field(metadata=meta(not_empty))


@convertibleclass
class StorageRequestObjectV1(RequestObject):
    FILE_ID = "fileId"
    fileId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class UploadFileRequestObjectV1(RequestObject):
    FILE = "file"
    FILE_DATA = "fileData"
    FILE_NAME = "fileName"
    FILE_SIZE = "fileSize"
    CONTENT_TYPE = "contentType"
    USER_ID = "userId"

    file: Any = required_field()
    fileData: Any = default_field()
    fileName: str = default_field()
    fileSize: int = default_field()
    contentType: str = default_field()
    userId: str = default_field()

    def post_init(self):
        self.fileData = self.file.read()
        self.fileName = secure_filename(self.file.filename)
        self.fileSize = len(self.fileData)
        self.contentType = self.file.content_type


@convertibleclass
class DownloadFileRequestObjectV1(StorageRequestObjectV1):
    pass


@convertibleclass
class GetSignedUrlRequestObjectV1(StorageRequestObjectV1):
    pass
