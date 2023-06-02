import hashlib
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import User, RoleAssignment
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.organization.component import OrganizationComponent
from extensions.organization.models.organization import Organization
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.revere.component import RevereComponent
from extensions.revere.exceptions import RevereErrorCodes
from extensions.revere.houndify.houndify import HoundifySDKError
from extensions.revere.models.revere import RevereTest, RevereTestResult
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils import inject
from sdk.tests.application_test_utils.test_utils import USER_ID

VALID_DEPLOYMENT_ID = "5eea14f0747a4aa3addf1bae"
RETRIEVE_AUDIO_PATH = (
    "extensions.revere.service.revere_service.RevereTestService.retrieve_audio_file"
)
SAMPLE_BUILD_NUMBER = "1151"
NOT_SUPPORTED_LANGUAGE_TAG_RESPONSE = {
    "CommandKind": "NoResultCommand",
    "SpokenResponse": "",
    "SpokenResponseLong": "Didn't get that!",
    "WrittenResponse": "Didn't get that!",
    "WrittenResponseLong": "Didn't get that!",
    "AutoListen": False,
    "ViewType": ["Native", "None"],
    "TranscriptionSearchURL": "http://www.google.com/#q=this%20is%20a%20test%20for%20an%20audio%20far%20in%20any%20p%20four%20a%20format",
}


def get_organization():
    return Organization(
        name="test",
        privacyPolicyUrl="privacy_url_val_organization",
        eulaUrl="eula_url_val_organization",
        termAndConditionUrl="term_val_organization",
    )


def retrieve_audio_file(filepath: str):
    test_audio_path = Path(__file__).parent.joinpath(filepath)
    with open(test_audio_path, "rb") as audio_file:
        d = BytesIO(audio_file.read())
        return d


def mocked_g():
    org_mock = MagicMock()
    org_mock.retrieve_organization.return_value = get_organization()

    def bind(binder):
        binder.bind_to_provider(DeploymentRepository, MagicMock())
        binder.bind_to_provider(OrganizationRepository, lambda: org_mock)

    inject.clear_and_configure(bind)

    gl = MagicMock()
    role = RoleAssignment.create_role(RoleName.USER, VALID_DEPLOYMENT_ID)
    gl.user = User(id=USER_ID, roles=[role])
    return gl


def get_sample_audio_submission_request():
    audio_s3 = {"bucket": "test", "key": "test.wav", "region": "cn"}
    data = {
        "type": "RevereTest",
        "deviceName": "iOS",
        "deploymentId": VALID_DEPLOYMENT_ID,
        "startDateTime": "2020-04-28T21:13:07Z",
        "audioResult": audio_s3,
        "initialWords": [
            "Parent",
            "Radio",
            "Nose",
            "River",
            "Helmet",
            "Music",
            "Sailor",
            "School",
            "Garden",
            "Coffee",
            "Drum",
            "House",
            "Machine",
            "Color",
            "Farmer",
        ],
    }
    return data


class RevereTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        RevereComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
    ]
    fixtures: list[str] = [Path(__file__).parent.joinpath("fixtures/revere.json")]
    VALID_USER_ID = "5e8f0c74b50aa9656c34789b"
    VALID_TEST_ID = "5eea217330fdc7bd52d352da"
    INVALID_TEST_ID = "6eea217330fdc7bd52d352da"
    NOT_PROCESSED_WORD_LIST_ID = "5ee7796831a65ca9a9e287e5"
    API_URL = "/api/extensions/v1beta/user"
    houdify_client_return = {
        "AllResults": [{"RawTranscription": "some translated words"}],
        "BuildInfo": {"BuildNumber": SAMPLE_BUILD_NUMBER},
    }

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(self.VALID_USER_ID)

    def post_audio_processing(self, data: dict):
        return self.flask_client.post(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/"
            f"{self.VALID_TEST_ID}/words/{self.NOT_PROCESSED_WORD_LIST_ID}/audio/",
            json=data,
            headers=self.headers,
        )

    def send_invalid_audio_processing_request(self, expected_error_code):
        data = get_sample_audio_submission_request()
        resp = self.post_audio_processing(data)

        self.assertEqual(400, resp.status_code)
        self.assertEqual(expected_error_code, resp.json["code"])
        return resp

    @patch("extensions.revere.router.revere_router.g", mocked_g())
    def test_start_revere_test_valid(self):
        resp = self.flask_client.post(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/start/",
            headers=self.headers,
        )
        self.assertEqual(201, resp.status_code)
        self.assertEqual(8, len(resp.json["wordLists"]))

    def test_process_audio_not_exist_invalid(self):
        data = get_sample_audio_submission_request()
        resp = self.post_audio_processing(data)
        self.assertEqual(404, resp.status_code)
        self.assertEqual(100003, resp.json["code"])

    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_process_audio_valid(self, hound_client, retrieve_audio_file_service):
        hound_client().finish.return_value = self.houdify_client_return
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/sample.mp4"
        )
        data = get_sample_audio_submission_request()
        resp = self.post_audio_processing(data)

        self.assertEqual(200, resp.status_code)
        hound_client().setHoundRequestInfo.assert_called_once_with(
            "InputLanguageIETFTag", "en-GB"
        )

        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/all/",
            headers=self.headers,
        )
        test = resp.json[0]
        latest_result = test[RevereTest.RESULTS][-1]
        self.assertEqual(
            self.NOT_PROCESSED_WORD_LIST_ID, latest_result[RevereTestResult.ID]
        )
        self.assertEqual(
            SAMPLE_BUILD_NUMBER, latest_result[RevereTestResult.BUILD_NUMBER]
        )

    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_process_audio_with_wrong_extension_valid(
        self, hound_client, retrieve_audio_file_service
    ):
        hound_client().finish.return_value = self.houdify_client_return
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/wrong_extension_sample.wav"
        )
        data = get_sample_audio_submission_request()
        resp = self.post_audio_processing(data)

        self.assertEqual(200, resp.status_code)
        hound_client().setHoundRequestInfo.assert_called_once_with(
            "InputLanguageIETFTag", "en-GB"
        )

        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/all/",
            headers=self.headers,
        )
        test = resp.json[0]
        latest_result = test[RevereTest.RESULTS][-1]
        self.assertEqual(
            self.NOT_PROCESSED_WORD_LIST_ID, latest_result[RevereTestResult.ID]
        )
        self.assertEqual(
            SAMPLE_BUILD_NUMBER, latest_result[RevereTestResult.BUILD_NUMBER]
        )

    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_process_audio_with_not_supported_language_tag(
        self, hound_client, retrieve_audio_file_service
    ):
        hound_client().finish.return_value = {
            "AllResults": [NOT_SUPPORTED_LANGUAGE_TAG_RESPONSE],
            "BuildInfo": {"BuildNumber": SAMPLE_BUILD_NUMBER},
        }
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/sample.mp4"
        )
        data = get_sample_audio_submission_request()
        resp = self.post_audio_processing(data)
        self.assertEqual(200, resp.status_code)

        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/all/",
            headers=self.headers,
        )
        test = resp.json[0]
        latest_result = test[RevereTest.RESULTS][-1]
        self.assertEqual(
            self.NOT_PROCESSED_WORD_LIST_ID, latest_result[RevereTestResult.ID]
        )
        self.assertEqual([""], latest_result[RevereTestResult.WORDS_RESULT])

    def test_finish_test_valid(self):
        resp = self.flask_client.post(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/{self.VALID_TEST_ID}/finish/",
            headers=self.headers,
        )
        self.assertEqual(200, resp.status_code)

    def test_retrieve_all_users_tests(self):
        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/all/",
            headers=self.headers,
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(resp.json))

    def test_retrieve_finished_user_tests(self):
        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/", headers=self.headers
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json))

    def test_export_test_result_valid(self):
        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/{self.VALID_TEST_ID}/",
            headers=self.headers,
        )
        self.assertEqual("text/csv", resp.mimetype)

    def test_export_test_result_failure(self):
        resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/{self.INVALID_TEST_ID}/",
            headers=self.headers,
        )
        self.assertEqual(404, resp.status_code)
        self.assertEqual(100003, resp.json["code"])

    @patch("extensions.revere.router.revere_router.g", mocked_g())
    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_full_revere_lifecycle(self, hound_client, retrieve_audio_file_service):
        # Creating test
        resp = self.flask_client.post(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/start/",
            headers=self.headers,
        )
        self.assertEqual(201, resp.status_code)
        self.assertEqual(8, len(resp.json["wordLists"]))
        test_id = resp.json[RevereTest.ID]

        # Submitting results
        hound_client().finish.return_value = {
            "AllResults": [{"RawTranscription": "River drum parent"}]
        }
        data = get_sample_audio_submission_request()
        for word_list in resp.json["wordLists"]:
            retrieve_audio_file_service.return_value = retrieve_audio_file(
                "fixtures/sample.mp4"
            )
            resp = self.flask_client.post(
                f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/"
                f"{test_id}/words/{word_list[RevereTestResult.ID]}/audio/",
                json=data,
                headers=self.headers,
            )

            self.assertEqual(200, resp.status_code)

        # Finishing test
        resp = self.flask_client.post(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/{test_id}/finish/",
            headers=self.headers,
        )
        self.assertEqual(200, resp.status_code)

        # Exporting test result
        export_resp = self.flask_client.get(
            f"{self.API_URL}/{self.VALID_USER_ID}/revere-test/{test_id}/",
            headers=self.headers,
        )
        self.assertEqual("text/csv", export_resp.mimetype)
        hashed_sample = (
            "22c9dab9ba3deeb276ffe08ef08c8171cb5c988aa925bc2cfa52b8e6450d94c8"
        )
        hashed_resp = hashlib.sha256(export_resp.data).hexdigest()
        self.assertEqual(hashed_sample, hashed_resp)

    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_process_audio_raises_exception(
        self, hound_client, retrieve_audio_file_service
    ):
        houndify_exception = HoundifySDKError()
        other_exception = Exception()
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/sample.mp4"
        )
        hound_client().finish.side_effect = [houndify_exception, other_exception]
        self.send_invalid_audio_processing_request(RevereErrorCodes.HOUNDIFY_ERROR)
        self.send_invalid_audio_processing_request(ErrorCodes.INVALID_REQUEST)

    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_process_wrong_audio_format_with_correct_extension_raises_exception(
        self, hound_client, retrieve_audio_file_service
    ):
        hound_client().finish.return_value = self.houdify_client_return
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/sample.wav"
        )
        resp = self.send_invalid_audio_processing_request(ErrorCodes.INVALID_REQUEST)
        self.assertEqual(
            "Invalid file format, check if the file is an mp4", resp.json["message"]
        )

    @patch(RETRIEVE_AUDIO_PATH)
    @patch("extensions.revere.houndify.houndify.StreamingHoundClient")
    def test_process_wrong_audio_format_with_wrong_extension_raises_exception(
        self, hound_client, retrieve_audio_file_service
    ):
        hound_client().finish.return_value = self.houdify_client_return
        retrieve_audio_file_service.return_value = retrieve_audio_file(
            "fixtures/wrong_extension_sample.mp4"
        )
        resp = self.send_invalid_audio_processing_request(ErrorCodes.INVALID_REQUEST)
        self.assertEqual(
            "Invalid file format, check if the file is an mp4", resp.json["message"]
        )
