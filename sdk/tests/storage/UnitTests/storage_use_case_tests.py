import unittest
from unittest.mock import MagicMock, patch

from werkzeug.datastructures import FileStorage

from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.storage.use_case.storage_request_objects import GetSignedUrlRequestObject
from sdk.storage.use_case.storage_use_cases import GetSignedUrlUseCase
from sdk.storage.use_case.storage_request_objects import (
    UploadFileRequestObject,
    UploadFileRequestObjectV1,
)

BUCKET = "Bucket"
FILE_NAME = "test_file.txt"
TEST_FILE_CONTENT = b""
CONTENT_TYPE = "text/plain"


class FileAdapterMock:
    instance = MagicMock()
    file_exist = MagicMock()

    def get_pre_signed_url(self, bucket_name: str, object_name: str):
        raise Exception("some test exception")


class GetSignedUrlUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        def bind(binder):
            binder.bind(PhoenixServerConfig, MagicMock())

        inject.clear_and_configure(bind)

    @patch("sdk.storage.use_case.storage_use_cases.get_file_adapter")
    def test_failure_get_pre_signed_url(self, get_file_adapter):
        get_file_adapter.return_value = FileAdapterMock()
        req_obj = GetSignedUrlRequestObject.from_dict(
            {
                GetSignedUrlRequestObject.BUCKET: "some_bucket",
                GetSignedUrlRequestObject.FILENAME: "some_filename",
                GetSignedUrlRequestObject.HOST: "some_host",
            }
        )
        with self.assertRaises(InvalidRequestException):
            GetSignedUrlUseCase().execute(req_obj)


class StorageRequestObjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.test_file = FileStorage(filename=FILE_NAME, content_type=CONTENT_TYPE)

    def test_object_with_file_only(self):
        data = {"file": self.test_file, "bucket": BUCKET}
        req = UploadFileRequestObject.from_dict(data)
        self.assertEqual("test_file.txt", req.filename)
        self.assertEqual(TEST_FILE_CONTENT, req.fileData)

    def test_object_filename_and_filedata(self):
        data = {
            "filename": FILE_NAME,
            "fileData": "SOME TEST CONTENT",
            "bucket": BUCKET,
        }
        req = UploadFileRequestObject.from_dict(data)
        self.assertIsNone(req.file)
        self.assertIsNone(req.mime)


class StorageRequestObjectV1TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.test_file = FileStorage(filename=FILE_NAME, content_type=CONTENT_TYPE)

    @patch("sdk.storage.use_case.storage_request_objects.secure_filename")
    def test_object_upload_success(self, mock_secure_name):
        data = {"file": self.test_file}
        req = UploadFileRequestObjectV1.from_dict(data)
        mock_secure_name.assert_called_once()
        self.assertEqual(req.fileData, TEST_FILE_CONTENT)
        self.assertEqual(req.fileSize, len(TEST_FILE_CONTENT))

    def test_object_no_file_error(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UploadFileRequestObjectV1.from_dict({})


if __name__ == "__main__":
    unittest.main()
