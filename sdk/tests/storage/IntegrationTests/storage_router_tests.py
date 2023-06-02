from io import BytesIO
from pathlib import Path
import requests

from minio import Minio

from sdk.auth.component import AuthComponent
from sdk.common.adapter.alibaba.oss_file_adapter import OSSFileStorageAdapter
from sdk.common.adapter.azure.azure_blob_storage_adapter import AzureBlobStorageAdapter
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.adapter.gcp.gcs_file_storage_adapter import GCSFileStorageAdapter
from sdk.common.adapter.minio.minio_config import MinioConfig
from sdk.common.adapter.minio.minio_file_storage_adapter import MinioFileStorageAdapter
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.storage.component import StorageComponent, StorageComponentV1
from sdk.tests.test_case import SdkTestCase

TEST_TEXT_FILE_NAME = "test_file.txt"
TEST_SVG_FILE_NAME = "test_file.svg"
AUTHORIZED_USER_ID = "5e8f0c74b50aa9656c34789a"
UNAUTHORIZED_USER_ID = "5e8f0c74b50aa9656c34789b"
NONEXISTENT_FILE_ID = "5acf0c74b50aa4656d348811"


def content_test_file(file_name=TEST_TEXT_FILE_NAME):
    with open(Path(__file__).parent.joinpath(file_name), "rb") as upload:
        return upload.read()


class StorageTestCase(SdkTestCase):
    ALLOWED_BUCKET: str
    ALLOWED_NOT_EXISTING_BUCKET: str
    DEFAULT_BUCKET: str
    NOT_ALLOWED_BUCKET: str
    fixtures = [Path(__file__).parent.joinpath("fixtures/users_dump.json")]
    components = [StorageComponent(), AuthComponent()]
    minio_config: MinioConfig

    @classmethod
    def setUpClass(cls) -> None:
        super(StorageTestCase, cls).setUpClass()
        cls.config: PhoenixServerConfig = read_config(cls.config_file_path)
        cls.minio_config = cls.config.server.adapters.minio

        # allowedBuckets should contain at least 2 records in config
        cls.ALLOWED_BUCKET = cls.config.server.storage.allowedBuckets[0]
        cls.ALLOWED_NOT_EXISTING_BUCKET = cls.config.server.storage.allowedBuckets[1]
        cls.NOT_ALLOWED_BUCKET = cls.ALLOWED_BUCKET + "notallowed"
        cls.DEFAULT_BUCKET = cls.config.server.storage.defaultBucket

        cls._init_buckets()

    @classmethod
    def _init_buckets(cls):
        client = Minio(
            cls.minio_config.url,
            cls.minio_config.accessKey,
            cls.minio_config.secretKey,
            secure=cls.minio_config.secure,
        )
        try:
            client.make_bucket(cls.ALLOWED_BUCKET)
            client.make_bucket(cls.NOT_ALLOWED_BUCKET)
        except:  # noqa:E722 assertRaises Exception too broad
            pass


class UploadTestCase(StorageTestCase):
    def test_upload_file(self):
        data = {
            "filename": TEST_TEXT_FILE_NAME,
            "mime": "application/yaml",
            "file": (BytesIO(content_test_file()), "file"),
        }
        rsp = self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.ALLOWED_BUCKET}",
            data=data,
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
            content_type="multipart/form-data",
        )
        self.assertEqual(rsp.status_code, 201)

    def test_upload_file_to_not_allowed_bucket_blocked(self):
        data = {
            "filename": TEST_TEXT_FILE_NAME,
            "mime": "application/yaml",
            "file": (BytesIO(content_test_file()), "file"),
        }
        rsp = self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.NOT_ALLOWED_BUCKET}",
            data=data,
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
            content_type="multipart/form-data",
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], 100007)

    def test_upload_file_to_not_existing_bucket_blocked(self):
        data = {
            "filename": TEST_TEXT_FILE_NAME,
            "mime": "application/yaml",
            "file": (BytesIO(content_test_file()), "file"),
        }
        rsp = self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.ALLOWED_NOT_EXISTING_BUCKET}",
            data=data,
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
            content_type="multipart/form-data",
        )
        self.assertEqual(rsp.status_code, 500)


class DownloadTestCase(StorageTestCase):
    def setUp(self):
        super().setUp()

        self._upload_content = content_test_file()

        data = {
            "filename": TEST_TEXT_FILE_NAME,
            "mime": "application/yaml",
            "file": (BytesIO(self._upload_content), "file"),
        }
        _ = self.flask_client.post(
            f"/api/storage/v1beta/upload/{self.ALLOWED_BUCKET}",
            data=data,
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
            content_type="multipart/form-data",
        )
        # some delay is necessary for

    def test_download_file(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/download/{self.ALLOWED_BUCKET}/{TEST_TEXT_FILE_NAME}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.content_type, "application/yaml")
        self.assertEqual(rsp.data, self._upload_content)

    def test_download_file_that_does_not_exist(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/download/{self.ALLOWED_BUCKET}/aaa",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], ErrorCodes.BUCKET_OR_FILE_DOES_NOT_EXIST)

    def test_download_url(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{self.ALLOWED_BUCKET}/{TEST_TEXT_FILE_NAME}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.content_type.startswith("text/html"))

    def test_download_signed_url(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/signed/url/{self.ALLOWED_BUCKET}/{TEST_TEXT_FILE_NAME}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        url: str = rsp.data.decode("utf8")
        rsp = requests.get(url)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.content, self._upload_content)

    def test_download_file_from_not_existing_bucket_blocked(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/download/{self.ALLOWED_NOT_EXISTING_BUCKET}/{TEST_TEXT_FILE_NAME}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], ErrorCodes.BUCKET_OR_FILE_DOES_NOT_EXIST)

    def test_download_file_from_not_allowed_bucket_blocked(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1beta/download/{self.NOT_ALLOWED_BUCKET}/{TEST_TEXT_FILE_NAME}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], 100007)


class CopyTestCase(StorageTestCase):
    def get_adapter(self, name):
        if name == "minio":
            return MinioFileStorageAdapter(self.minio_config)
        elif name == "gcs":
            return GCSFileStorageAdapter(self.config.server.adapters.gcs)
        elif name == "azure":
            return AzureBlobStorageAdapter(self.config.server.adapters.azureBlobStorage)
        elif name == "oss":
            return OSSFileStorageAdapter(self.config.server.adapters.oss)

    def upload_file_and_confirm(self, adapter: FileStorageAdapter):
        file_path = Path(__file__).parent.joinpath(TEST_TEXT_FILE_NAME)
        with open(file_path, "rb") as file:
            adapter.upload_file(self.DEFAULT_BUCKET, TEST_TEXT_FILE_NAME, file)

        url = adapter.get_pre_signed_url(self.DEFAULT_BUCKET, TEST_TEXT_FILE_NAME)
        self.assertIsNotNone(url)

    def test_success_copy_minio(self):
        adapter_name = "minio"
        adapter = self.get_adapter(adapter_name)
        self.upload_file_and_confirm(adapter)

        new_filename = f"{adapter_name}_{TEST_TEXT_FILE_NAME}"
        adapter.copy(TEST_TEXT_FILE_NAME, new_filename, self.DEFAULT_BUCKET)
        url = adapter.get_pre_signed_url(self.DEFAULT_BUCKET, new_filename)
        self.assertIsNotNone(url)

    # TODO find a way to test other adapters


class StorageV1TestCase(SdkTestCase):
    fixtures = [Path(__file__).parent.joinpath("fixtures/users_dump.json")]
    components = [StorageComponentV1(), AuthComponent()]
    DEFAULT_BUCKET: str
    minio_config: MinioConfig

    @classmethod
    def setUpClass(cls) -> None:
        super(StorageV1TestCase, cls).setUpClass()
        cls.config: PhoenixServerConfig = read_config(cls.config_file_path)
        cls.minio_config = cls.config.server.adapters.minio
        cls.DEFAULT_BUCKET = cls.config.server.storage.defaultBucket

        cls._init_buckets()

    @classmethod
    def _init_buckets(cls):
        client = Minio(
            cls.minio_config.url,
            cls.minio_config.accessKey,
            cls.minio_config.secretKey,
            secure=cls.minio_config.secure,
        )
        try:
            client.make_bucket(cls.DEFAULT_BUCKET)
        except:  # noqa:E722 assertRaises Exception too broad
            pass

    def upload_test_file(
        self, user_id=AUTHORIZED_USER_ID, file_name=TEST_TEXT_FILE_NAME
    ):
        data = {
            "file": (BytesIO(content_test_file(file_name)), file_name),
        }
        rsp = self.flask_client.post(
            f"/api/storage/v1/upload",
            data=data,
            headers=self.get_headers_for_token(identity=user_id),
            content_type="multipart/form-data",
        )
        return rsp


class UploadV1TestCase(StorageV1TestCase):
    def test_success_upload_file(self):
        rsp = self.upload_test_file()
        self.assertEqual(rsp.status_code, 201)

    def test_failure_unauthorized_upload_file(self):
        rsp = self.upload_test_file(UNAUTHORIZED_USER_ID)
        self.assertEqual(rsp.status_code, 401)


class DownloadV1TestCase(StorageV1TestCase):
    def setUp(self):
        super().setUp()

        self._upload_text_file_content = content_test_file(TEST_TEXT_FILE_NAME)
        self._upload_svg_file_content = content_test_file(TEST_SVG_FILE_NAME)
        self._uploaded_text_file_id = self.upload_test_file(
            file_name=TEST_TEXT_FILE_NAME
        ).json.get("id")
        self._uploaded_svg_file_id = self.upload_test_file(
            file_name=TEST_SVG_FILE_NAME
        ).json.get("id")

    def test_download_file(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1/download/{self._uploaded_text_file_id}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.content_type.startswith("text/plain"))
        self.assertEqual(rsp.data, self._upload_text_file_content)

    def test_content_type_detection(self):
        files = {
            TEST_TEXT_FILE_NAME: (
                self._uploaded_text_file_id,
                self._upload_text_file_content,
                "text/plain",
            ),
            TEST_SVG_FILE_NAME: (
                self._uploaded_svg_file_id,
                self._upload_svg_file_content,
                "image/svg+xml",
            ),
        }
        for file_name in files:
            rsp = self.flask_client.get(
                f"/api/storage/v1/download/{files[file_name][0]}",
                headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
            )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.content_type.startswith(files[file_name][2]))
        self.assertEqual(rsp.data, files[file_name][1])

    def test_download_nonexistent_file(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1/download/{NONEXISTENT_FILE_ID}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 404)
        self.assertEqual(rsp.json["code"], ErrorCodes.BUCKET_OR_FILE_DOES_NOT_EXIST)

    def test_get_signed__url(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1/signed-url/{self._uploaded_text_file_id}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertIsNotNone(rsp.json.get("url"))

    def test_download_file_from_signed_url(self):
        rsp = self.flask_client.get(
            f"/api/storage/v1/signed-url/{self._uploaded_text_file_id}",
            headers=self.get_headers_for_token(identity=AUTHORIZED_USER_ID),
        )
        download_url: str = rsp.json.get("url")
        rsp = requests.get(download_url)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.content, self._upload_text_file_content)
