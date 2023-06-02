from io import BytesIO
from pathlib import Path
from extensions.authorization.component import AuthorizationComponent
from extensions.organization.component import OrganizationComponent

from minio import Minio

from extensions.deployment.component import DeploymentComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.adapter.minio.minio_config import MinioConfig
from sdk.common.utils.validators import validate_object_id
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import read_config
from sdk.storage.component import StorageComponentV1
from sdk.tests.application_test_utils.test_utils import SDK_CONFIG_PATH

USER_ID = "5e8f0c74b50aa9656c34789c"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
SAMPLE_FILE_NAME = "sample.png"
LIBRARY_ID = "huma_image_library"


def get_sample_file_content(file_name=SAMPLE_FILE_NAME):
    with open(Path(__file__).parent.joinpath(f"fixtures/{file_name}"), "rb") as upload:
        return upload.read()


class FileLibraryTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        StorageComponentV1(),
        OrganizationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployment_dump.json")]

    DEFAULT_BUCKET: str
    minio_config: MinioConfig

    def setUp(self) -> None:
        super(FileLibraryTests, self).setUp()
        self.config: PhoenixServerConfig = read_config(SDK_CONFIG_PATH)
        self.minio_config = self.config.server.adapters.minio
        self.DEFAULT_BUCKET = self.config.server.storage.defaultBucket
        self._init_buckets()

    def _init_buckets(self):
        client = Minio(
            self.minio_config.url,
            self.minio_config.accessKey,
            self.minio_config.secretKey,
            secure=self.minio_config.secure,
        )
        try:
            client.make_bucket(self.DEFAULT_BUCKET)
        except:  # noqa:E722 assertRaises Exception too broad
            pass

    def upload_sample_file(
        self, user_id=USER_ID, file_name=SAMPLE_FILE_NAME, file_content=None
    ):
        if file_content is None:
            data = {
                "file": (BytesIO(get_sample_file_content(file_name)), file_name),
            }
        else:
            data = {
                "file": (BytesIO(file_content), file_name),
            }
        rsp = self.flask_client.post(
            f"/api/storage/v1/upload",
            data=data,
            headers=self.get_headers_for_token(identity=user_id),
            content_type="multipart/form-data",
        )
        return rsp

    @staticmethod
    def sample_csv_data(num_rows=10):
        column_names = ["key, en"]
        rows = [f"key{row}, test{row}" for row in range(1, num_rows + 1)]
        return "\n".join(column_names + rows).encode("utf-8")

    def add_files_to_library(self, file_ids, library_id, deployment_id):
        data = {
            "fileIds": file_ids,
            "deploymentId": deployment_id,
            "libraryId": library_id,
        }
        rsp = self.flask_client.post(
            f"/api/extensions/v1beta/deployment/file-library",
            json=data,
            headers=self.get_headers_for_token(identity=USER_ID),
        )
        return rsp

    def retrieve_files_in_library(self, library_id):
        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/deployment/file-library/{library_id}",
            headers=self.get_headers_for_token(identity=USER_ID),
        )
        return rsp

    def test_file_library_flow(self):
        rsp = self.upload_sample_file()
        self.assertEqual(rsp.status_code, 201)
        file_id = rsp.json.get("id")
        self.assertTrue(validate_object_id(file_id))

        rsp = self.add_files_to_library(
            file_ids=[file_id], library_id=LIBRARY_ID, deployment_id=DEPLOYMENT_ID
        )
        self.assertEqual(rsp.status_code, 200)

        rsp = self.retrieve_files_in_library(LIBRARY_ID)
        self.assertEqual(rsp.status_code, 200)
        files = rsp.json.get("files")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].get("fileName"), SAMPLE_FILE_NAME)
        self.assertEqual(files[0].get("metadata").get("libraryId"), LIBRARY_ID)

    def test_file_library_csv_upload_success(self):
        csv_content = self.sample_csv_data()
        rsp = self.upload_sample_file(file_name="sample.csv", file_content=csv_content)
        self.assertEqual(rsp.status_code, 201)
        file_id = rsp.json.get("id")
        self.assertTrue(validate_object_id(file_id))

        rsp = self.add_files_to_library(
            file_ids=[file_id],
            library_id="huma_options_library",
            deployment_id=DEPLOYMENT_ID,
        )
        self.assertEqual(rsp.status_code, 200)

    def test_file_library_xlsx_upload_unsuccessful(self):
        xlsx_content = b"wrong xlsx content"
        rsp = self.upload_sample_file(
            file_name="sample.xlsx", file_content=xlsx_content
        )
        self.assertEqual(rsp.status_code, 201)
        file_id = rsp.json.get("id")
        self.assertTrue(validate_object_id(file_id))

        rsp = self.add_files_to_library(
            file_ids=[file_id],
            library_id="huma_options_library",
            deployment_id=DEPLOYMENT_ID,
        )
        self.assertEqual(rsp.status_code, 403)
