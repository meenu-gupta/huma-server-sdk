from pathlib import Path

from extensions.authorization.callbacks import setup_storage_auth
from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import TEST_FILE_PATH
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.storage.callbacks.binder import PostStorageSetupEvent
from sdk.storage.component import StorageComponent

VALID_USER1_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER2_ID = "601919b5c03550c421c075eb"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"
INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"
PROXY_ID = "606eba3a2c94383d620b52ad"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"


class PersonalDocumentsTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        StorageComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    personal_documents = [
        {
            "name": "Second vaccination dose card",
            "fileType": "PHOTO",
            "fileObject": {"bucket": "String", "key": "String"},
        },
        {
            "name": "First vaccination dose card",
            "fileType": "PDF",
            "fileObject": {"bucket": "String", "key": "String"},
        },
    ]

    def setUp(self):
        super().setUp()
        self.test_server.event_bus.subscribe(PostStorageSetupEvent, setup_storage_auth)
        self.headers_user1 = self.get_headers_for_token(VALID_USER1_ID)
        self.headers_user2 = self.get_headers_for_token(VALID_USER2_ID)
        self.headers_contributor = self.get_headers_for_token(VALID_CONTRIBUTOR_ID)
        self.base_route = "/api/extensions/v1beta/user"

    def test_success_create_personal_document(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        rsp = self.flask_client.post(
            path, json=self.personal_documents[0], headers=self.headers_user1
        )
        self.assertEqual(rsp.status_code, 201)
        self.assertEqual(rsp.json["id"], VALID_USER1_ID)

    def test_success_retrieve_personal_documents(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        for document in self.personal_documents:
            rsp = self.flask_client.post(
                path, json=document, headers=self.headers_user1
            )
            self.assertEqual(rsp.status_code, 201)
        rsp = self.flask_client.get(path, headers=self.headers_user1)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(len(rsp.json), 2)

    def test_failure_security_add_personal_document_for_other_user(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        rsp = self.flask_client.post(
            path, json=self.personal_documents[0], headers=self.headers_user2
        )
        self.assertEqual(rsp.status_code, 403)

    def test_failure_security_retrieve_personal_of_other_user(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        rsp = self.flask_client.post(
            path, json=self.personal_documents[0], headers=self.headers_user1
        )
        self.assertEqual(rsp.status_code, 201)
        rsp = self.flask_client.get(path, headers=self.headers_user2)
        self.assertEqual(rsp.status_code, 403)

    def test_success_contributor_can_add_personal_documents_for_user(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        rsp = self.flask_client.post(
            path, json=self.personal_documents[0], headers=self.headers_contributor
        )
        self.assertEqual(rsp.status_code, 201)

    def test_success_contributor_can_retrieve_user_personal_documents(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        for document in self.personal_documents:
            rsp = self.flask_client.post(
                path, json=document, headers=self.headers_user1
            )
            self.assertEqual(rsp.status_code, 201)
        rsp = self.flask_client.get(path, headers=self.headers_contributor)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(len(rsp.json), 2)

    def test_failure_retrieve_invalid_user_id(self):
        path = f"{self.base_route}/{INVALID_USER_ID}/document"
        rsp = self.flask_client.post(
            path, json=self.personal_documents[0], headers=self.headers_user1
        )
        self.assertEqual(rsp.status_code, 404)

    def test_failure_create_personal_document_wrong_file_type(self):
        document = {
            "name": "Second vaccination dose card",
            "fileType": "WRONG_FILE",
            "fileObject": {"bucket": "String", "key": "String"},
        }
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        rsp = self.flask_client.post(path, json=document, headers=self.headers_user1)
        self.assertEqual(rsp.status_code, 403)

    def test_failure_create_personal_document_name_too_long(self):
        document = {
            "name": "A" * 256,
            "fileType": "PDF",
            "fileObject": {"bucket": "String", "key": "String"},
        }
        path = f"{self.base_route}/{VALID_USER1_ID}/document"
        rsp = self.flask_client.post(path, json=document, headers=self.headers_user1)
        self.assertEqual(rsp.status_code, 403)

    def test_success_upload_personal_documents(self):
        filename = f"user/{VALID_USER1_ID}/PersonalDocuments/"
        with open(TEST_FILE_PATH, "rb") as file:
            data = {
                "filename": filename,
                "mime": "application/octet-stream",
                "file": file,
            }
            rsp = self.flask_client.post(
                f"/api/storage/v1beta/upload/{self.config.server.storage.defaultBucket}",
                data=data,
                headers=self.get_headers_for_token(VALID_USER1_ID),
                content_type="multipart/form-data",
            )
            self.assertEqual(201, rsp.status_code)

    def test_success_download_deployment_logo(self):
        url = f"/api/storage/v1beta/signed/url/{self.config.server.storage.defaultBucket}/deployment/{DEPLOYMENT_ID}/logo.png"
        rsp = self.flask_client.get(url, headers=self.get_headers_for_token(PROXY_ID))
        self.assertNotEqual(403, rsp.status_code)
