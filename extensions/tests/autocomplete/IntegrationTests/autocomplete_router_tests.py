import io
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from extensions.authorization.component import AuthorizationComponent
from extensions.autocomplete.component import AutocompleteComponent
from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.autocomplete.models.autocomplete_module import AutocompleteModule
from extensions.autocomplete.router.autocomplete_requests import (
    SearchAutocompleteRequestObject,
)
from extensions.common.s3object import S3Object
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.abstract_permission_test_case import (
    AbstractPermissionTestCase,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import BUCKET_NAME
from sdk.auth.component import AuthComponent
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils import inject
from sdk.storage.component import StorageComponent
from sdk.versioning.component import VersionComponent

SUPER_ADMIN_USER_ID = "5e8f0c74b50aa9656c34789b"
MAIN_MODULE_PATH = (
    "extensions.autocomplete.models.autocomplete_module.AutocompleteModule"
)


def get_autocomplete_request_dict() -> dict:
    return {
        SearchAutocompleteRequestObject.LIST_ENDPOINT_ID: "Medications",
        SearchAutocompleteRequestObject.SEARCH: "alfa",
    }


class AutocompleteRouterTestCase(AbstractPermissionTestCase):
    SERVER_VERSION = "1.3.1"
    API_VERSION = "v1"
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        AutocompleteComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
        StorageComponent(),
        VersionComponent(server_version=SERVER_VERSION, api_version=API_VERSION),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    override_config = {"server.deployment.enableAuthz": "true"}

    def _upload_auto_complete_json_files(self, path):
        m = inject.instance(FileStorageAdapter)
        with open(path.joinpath("fixtures/assets/file_list.json")) as myfile:
            files = json.load(myfile)
        metadata = []
        for file_object in files:
            file_path = path.joinpath(f"fixtures/assets/{file_object['filename']}")
            key_name = f"static/autocomplete/{file_object['filename']}"
            with open(file_path, "rb") as file:
                content = file.read()
                m.upload_file(BUCKET_NAME, key_name, io.BytesIO(content), len(content))
            metadata.append(
                {
                    AutocompleteMetadata.MODULE_ID: file_object["moduleId"],
                    AutocompleteMetadata.S3_OBJECT: {
                        S3Object.BUCKET: BUCKET_NAME,
                        S3Object.KEY: key_name,
                        S3Object.REGION: "eu",
                    },
                    AutocompleteMetadata.LANGUAGE: file_object["language"],
                }
            )

        self.flask_client.post(
            f"{self.base_path}/update",
            json={"metadata": metadata},
            headers=self.get_headers_for_token(SUPER_ADMIN_USER_ID),
        )

    def setUp(self):
        super().setUp()
        self.base_path = "/api/autocomplete/v1beta"
        self.user_id = "5e8f0c74b50aa9656c34789c"
        self.headers = self.get_headers_for_token(self.user_id)
        self.headers_with_locale = {
            **self.get_headers_for_token(self.user_id),
            "x-hu-locale": "de",
        }
        self._upload_auto_complete_json_files(Path(__file__).parent)

    def call_search(
        self, module_name, search, exact_word: bool = False, headers: dict = None
    ):
        data = {
            SearchAutocompleteRequestObject.LIST_ENDPOINT_ID: module_name,
            SearchAutocompleteRequestObject.SEARCH: search,
            SearchAutocompleteRequestObject.EXACT_WORD: exact_word,
        }
        return self.flask_client.post(
            f"{self.base_path}/search", json=data, headers=headers or self.headers
        )


class MedicationsAutocompleteTestCase(AutocompleteRouterTestCase):
    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success_search_autocomplete_result(self, read_local_file_mock):
        rsp = self.call_search("Medications", "Car")
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 9)
        self.assertIn("Carbamazepine", rsp.json)
        self.assertIn("Dacarbazine", rsp.json)

    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success_search_autocomplete_result_de(self, read_local_file_mock):
        rsp = self.call_search("Medications", "mycin", headers=self.headers_with_locale)
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 5)
        self.assertIn("Bleomycin", rsp.json)
        self.assertIn("Mitomycin", rsp.json)

    def test_success_search_autocomplete_result_invalid_language(self):
        headers = self.get_headers_for_token(self.user_id)
        headers["x-hu-locale"] = "invalid-lang"
        rsp = self.call_search("Medications", "mycin", headers=headers)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 5)
        self.assertIn("Bleomycin", rsp.json)
        self.assertIn("Mitomycin", rsp.json)


class SymptomsAutocompleteTestCase(AutocompleteRouterTestCase):
    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success_search_autocomplete_result(self, read_local_file_mock):
        rsp = self.call_search("Symptoms", "joint")
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 18)
        self.assertIn("Joint ache", rsp.json)
        self.assertIn("Joint stiffness", rsp.json)

    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success_search_autocomplete_result_de(self, read_local_file_mock):
        rsp = self.call_search("Symptoms", "öger", headers=self.headers_with_locale)
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 5)
        self.assertIn("Entwicklungsverzögerung", rsp.json)
        self.assertIn("Verzögerte Grobmotorik", rsp.json)


class VaccinesAutocompleteTestCase(AutocompleteRouterTestCase):
    def _update_metadata(self):
        key_name = "static/autocomplete/vaccine.json"
        data = {
            "filename": key_name,
            "mime": "application/json",
            "file": (BytesIO(b'["abcdef"]'), "vaccine.json"),
        }
        headers = self.get_headers_for_token(SUPER_ADMIN_USER_ID)
        rsp = self.flask_client.post(
            f"/api/storage/v1beta/upload/{BUCKET_NAME}",
            data=data,
            headers=headers,
            content_type="multipart/form-data",
        )

        metadata = {
            AutocompleteMetadata.MODULE_ID: "AZVaccineBatchNumber",
            AutocompleteMetadata.S3_OBJECT: {
                S3Object.BUCKET: BUCKET_NAME,
                S3Object.KEY: key_name,
                S3Object.REGION: "",
            },
            AutocompleteMetadata.LANGUAGE: "en",
        }
        self.flask_client.post(
            f"{self.base_path}/update", json={"metadata": [metadata]}, headers=headers
        )
        self.assertEqual(rsp.status_code, 201)

    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success_search_autocomplete_result(self, read_local_file_mock):
        rsp = self.call_search("AZVaccineBatchNumber", "ABV3922", exact_word=True)
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 1)
        self.assertIn("ABV3922", rsp.json)

    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_failure_search_autocomplete_result_not_exact_word(
        self, read_local_file_mock
    ):
        rsp = self.call_search("AZVaccineBatchNumber", "ABV3922")
        read_local_file_mock.assert_not_called()
        self.assertEqual(400, rsp.status_code)

    def test_failure_search_autocomplete_result_invalid_module(self):
        request_obj = get_autocomplete_request_dict()
        request_obj[SearchAutocompleteRequestObject.LIST_ENDPOINT_ID] = "invalid one"
        rsp = self.flask_client.post(
            f"{self.base_path}/search",
            json=request_obj,
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)

    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success_search_autocomplete_result_de(self, read_local_file_mock):
        rsp = self.call_search(
            "AZVaccineBatchNumber",
            "ABV3922",
            exact_word=True,
            headers=self.headers_with_locale,
        )
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 1)

    @patch.object(AutocompleteModule, "read_from_local_file")
    def test_success__search_autocomplete_result_adding_new_vaccine_number(
        self, read_local_file_mock
    ):
        rsp = self.call_search("AZVaccineBatchNumber", "abcdef", exact_word=True)
        read_local_file_mock.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 0)

        self._update_metadata()

        rsp = self.call_search("AZVaccineBatchNumber", "abcdef", exact_word=True)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 1)
        self.assertIn("abcdef", rsp.json)

    @patch.object(AutocompleteModule, "_is_cache_valid")
    def test_success_search_autocomplete_result_fallback_to_local_file(
        self, is_cache_valid
    ):
        self.mongo_database.drop_collection("autocomplete")
        rsp = self.call_search("AZVaccineBatchNumber", "ABV3922", exact_word=True)
        is_cache_valid.assert_not_called()
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(len(rsp.json), 1)
        self.assertIn("ABV3922", rsp.json)
