import uuid
from copy import copy
from typing import Optional
from unittest.mock import MagicMock, patch

from bson import ObjectId
from extensions.authorization.models.user import BoardingStatus, User
from extensions.authorization.repository.mongo_user_repository import (
    MongoUserRepository,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.router.deployment_requests import (
    WithdrawEConsentRequestObject,
)
from extensions.exceptions import UserErrorCodes
from extensions.tests.deployment.IntegrationTests.deployment_router_tests import (
    AbstractDeploymentTestCase,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from extensions.tests.shared.test_helpers import simple_econsent, simple_econsent_log
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils.validators import validate_object_id


class MockFunction:
    update_econsent_pdf_location = MagicMock()
    update_econsent_pdf_location.return_value = True


class CreateEConsentTestCase(AbstractDeploymentTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(CreateEConsentTestCase, cls).setUpClass()
        cls.deployment_id = "5d386cc6ff885918d96edb2c"
        cls.createEConsentBody = simple_econsent()
        cls.base_path = "/api/extensions/v1beta/deployment"

    def test_econsent_creation_and_check_section_counts(self):
        body = self.createEConsentBody
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.deployment_id}/econsent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(201, rsp.status_code)

        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}/econsent",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(4, len(rsp.json[EConsent.SECTIONS]))

    def test_econsent_creation_with_id(self):
        body = copy(self.createEConsentBody)
        body["id"] = uuid.uuid4()
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.deployment_id}/econsent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_econsent_creation_with_date(self):
        body = copy(self.createEConsentBody)
        body["createDateTime"] = "2020-04-07T17:05:51"
        rsp = self.flask_client.post(
            f"{self.base_path}/{self.deployment_id}/econsent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)

    def test_econsent_creation_for_not_existing_deployment(self):
        body = copy(self.createEConsentBody)
        deployment_id = "5d386cc6ff885918d96edb5c"
        rsp = self.flask_client.post(
            f"{self.base_path}/{deployment_id}/econsent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)

    def _test_failure_econsent_creation_403_issue(self, body):
        deployment_id = "5d386cc6ff885918d96edb5c"
        rsp = self.flask_client.post(
            f"{self.base_path}/{deployment_id}/econsent",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_econsent_creation_for_co_existing_thumbnail_url_and_location(self):
        body = copy(self.createEConsentBody)
        body[EConsent.SECTIONS][0]["thumbnailUrl"] = "thumbnailUrl.png"
        self._test_failure_econsent_creation_403_issue(body)

    def test_failure_econsent_creation_for_co_existing_video_url_and_location(self):
        body = copy(self.createEConsentBody)
        body[EConsent.SECTIONS][2]["videoUrl"] = "videoLocation.mp4"
        self._test_failure_econsent_creation_403_issue(body)

    def test_failure_econsent_creation_for_existing_video_url_in_type_image(self):
        body = copy(self.createEConsentBody)
        body[EConsent.SECTIONS][0]["videoUrl"] = "videoLocation.mp4"
        self._test_failure_econsent_creation_403_issue(body)

    def test_failure_econsent_creation_for_missing_content_type(self):
        body = copy(self.createEConsentBody)
        body[EConsent.SECTIONS][0].pop("contentType")
        self._test_failure_econsent_creation_403_issue(body)

    def test_failure_econsent_creation_for_thumbnail_location_invalid_type(self):
        body = copy(self.createEConsentBody)
        body[EConsent.SECTIONS][0]["thumbnailLocation"] = "invalid_s3_object"
        self._test_failure_econsent_creation_403_issue(body)

    def test_failure_econsent_creation_missing_section(self):
        body = copy(self.createEConsentBody)
        del body[EConsent.SECTIONS]
        self._test_failure_econsent_creation_403_issue(body)


class RetrieveEConsentTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.deployment_id = "5d386cc6ff885918d96edb2c"
        self.latest_econsent_id = "5e9443789911c97c0b639444"

    def test_latest_econsent_retrieve(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}/econsent",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(self.latest_econsent_id, rsp.json["id"])

    def test_retrieve_econsent_if_econsent_does_not_exist(self):
        self.remove_econsent()
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/{self.deployment_id}/econsent",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(rsp.json, {})

    def test_latest_econsent_retrieve_deployment_not_exist(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/deployment/5d386cc6ff885918d96edc2c/econsent",
            headers=self.headers,
        )
        self.assertEqual(404, rsp.status_code)


class SignEConsentTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.deployment_id = "5d386cc6ff885918d96edb2c"
        self.user_id = "5ffee8a004ae8ffa8e721114"
        self.user_id2 = "5e8f0c74b50aa9656c34789c"
        self.admin_id = "5e8f0c74b50aa9656c34789b"
        self.latest_econsent_id = "5e9443789911c97c0b639444"
        self.admin_headers = self.get_headers_for_token(self.admin_id)
        self.headers = self.get_headers_for_token(self.user_id)

    @patch("extensions.deployment.tasks.update_econsent_pdf_location.delay")
    def test_success_sign_econsent(self, mock_func):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/sign",
            headers=self.headers,
            json=simple_econsent_log(),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertTrue(validate_object_id(rsp.json["id"]))
        mock_func.assert_called_once()
        mock_func.reset_mock()
        return rsp.json["id"]

    @patch("extensions.deployment.tasks.update_econsent_pdf_location.delay")
    def test_success_sign_consent_replace_translation_placeholders(self, mock_func):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/sign",
            headers=self.headers,
            json=simple_econsent_log(),
        )
        self.assertEqual(201, rsp.status_code)
        arguments = mock_func.call_args.kwargs
        expected_strs = {
            "participant_name": "Print name of participant:",
            "date_signature": "Date and time of signature:",
            "signature": "Signature of participant:",
            "no": "No",
            "yes": "Yes",
        }
        self.assertEqual(expected_strs, arguments["other_strings"])
        mock_func.reset_mock()

    def test_failure_sign_invalid_econsent(self):
        econsent_id = "5e9443789911c97c0b639445"
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{econsent_id}/sign",
            headers=self.headers,
            json=simple_econsent_log(),
        )
        self.assertEqual(404, rsp.status_code)

    def test_failure_sign_econsent_again(self):
        user_id = "5e8f0c74b50aa9656c34789c"
        headers = self.get_headers_for_token(user_id)
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{user_id}/econsent/{self.latest_econsent_id}/sign",
            headers=headers,
            json=simple_econsent_log(),
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_sign_econsent_with_invalid_question_type(self):
        econsent = copy(simple_econsent_log())
        econsent[EConsentLog.ADDITIONAL_CONSENT_ANSWERS].update(
            {"invalid_question": "answer"}
        )
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/sign",
            headers=self.headers,
            json=econsent,
        )
        self.assertEqual(400, rsp.status_code)

    def test_failure_offboard_when_not_consenting(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/sign",
            headers=self.headers,
            json={**simple_econsent_log(), EConsentLog.CONSENT_OPTION: 0},
        )
        self.assertEqual(412, rsp.status_code)

    def test_success_withdraw_econsent(self):
        log_id = self.test_success_sign_econsent()
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/withdraw",
            headers=self.headers,
            json={WithdrawEConsentRequestObject.LOG_ID: log_id},
        )
        self.assertEqual(200, rsp.status_code)

        self._assert_off_boarded(
            self.user_id, BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF
        )

    def test_failure_withdraw_econsent_different_user_authtoken(self):
        log_id = self.test_success_sign_econsent()
        invalid_headers = self.get_headers_for_token(self.user_id2)
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/withdraw",
            headers=invalid_headers,
            json={WithdrawEConsentRequestObject.LOG_ID: log_id},
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_withdraw_econsent_different_user_authtoken_user_id(self):
        log_id = self.test_success_sign_econsent()
        invalid_headers = self.get_headers_for_token(self.user_id2)
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id2}/econsent/{self.latest_econsent_id}/withdraw",
            headers=invalid_headers,
            json={WithdrawEConsentRequestObject.LOG_ID: log_id},
        )
        self.assertEqual(404, rsp.status_code)

    def test_success_withdraw_econsent_multiple_signed_consent(self):
        self.test_success_sign_econsent()
        self._update_deployment_ecosent()
        log_id = self.test_success_sign_econsent()

        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/withdraw",
            headers=self.headers,
            json={WithdrawEConsentRequestObject.LOG_ID: log_id},
        )
        self.assertEqual(200, rsp.status_code)

        self._assert_off_boarded(
            self.user_id, BoardingStatus.ReasonOffBoarded.USER_WITHDRAW_EICF
        )

    def test_failure_withdraw_econsent_outdated(self):
        log_id = self.test_success_sign_econsent()
        self._update_deployment_ecosent()
        self.test_success_sign_econsent()

        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/withdraw",
            headers=self.headers,
            json={WithdrawEConsentRequestObject.LOG_ID: log_id},
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(rsp.json["code"], UserErrorCodes.OUTDATED_ECONSENT)

    def test_failure_withdraw_econsent_invalid_econsent_id(self):
        invalid_econsent_id = "5e8f0c74b50aa9656c34789c"
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{invalid_econsent_id}/withdraw",
            headers=self.headers,
            json={WithdrawEConsentRequestObject.LOG_ID: "5e8f0c74b50aa9656c34789c"},
        )
        self.assertEqual(404, rsp.status_code)

    def test_failure_withdraw_econsent_invalid_request(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{self.latest_econsent_id}/withdraw",
            headers=self.headers,
        )
        self.assertEqual(400, rsp.status_code)

    def _assert_off_boarded(self, user_id: str, reason: int):
        res = self.get_profile(user_id)
        boarding_status = res[User.BOARDING_STATUS]
        self.assertIsNotNone(boarding_status)
        self.assertEqual(
            boarding_status[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED
        )
        self.assertEqual(
            boarding_status[BoardingStatus.REASON_OFF_BOARDED],
            reason,
        )

    def enable_off_boarding(self, custom_duration: str = None):
        body = {"features": {"offBoarding": True}, "duration": custom_duration or "P1D"}
        rsp = self.flask_client.put(
            f"{self.deployment_route}/deployment/{self.deployment_id}",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)

    def get_profile(self, user_id: str):
        return self.mongo_database[MongoUserRepository.USER_COLLECTION].find_one(
            {User.ID_: ObjectId(user_id)}
        )

    def _assert_expected_module_result_status_code(
        self, expected_status_code: int, headers: Optional[dict[str, str]] = None
    ):
        if not headers:
            headers = self.get_headers_for_token(self.user_id)
        data = {
            **common_fields(),
            "type": "BloodPressure",
            "diastolicValue": 80,
            "systolicValue": 80,
        }
        rsp = self.flask_client.post(
            f"api/extensions/v1beta/user/{self.user_id}/module-result/BloodPressure",
            headers=headers,
            json=[data],
        )
        self.assertEqual(expected_status_code, rsp.status_code)

    def _update_deployment_ecosent(self):

        body = simple_econsent()
        rsp = self.flask_client.post(
            f"{self.deployment_route}/deployment/{self.deployment_id}/econsent",
            json=body,
            headers=self.admin_headers,
        )
        self.assertEqual(201, rsp.status_code)


class RetrieveEConsentPdfTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.deployment_id = "5d386cc6ff885918d96edb2c"
        self.user_id = "5e8f0c74b50aa9656c34789c"
        self.user_id2 = "5ffee8a004ae8ffa8e721114"
        self.manager_id = "5ffca6d91882ddc1cd8ab94f"
        self.latest_econsent_id = "5e9443789911c97c0b639444"
        self.headers_for_user = self.get_headers_for_token(self.user_id)
        self.headers_for_user2 = self.get_headers_for_token(self.user_id2)
        self.headers_for_manager = self.get_headers_for_token(self.manager_id)

    def test_retrieve_econsent_pdf_for_manager(self):
        rsp = self.flask_client.get(
            f"{self.deployment_route}/user/{self.manager_id}/econsent/{self.latest_econsent_id}/pdf",
            headers=self.headers_for_manager,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertTrue(validate_object_id(next(iter(rsp.json))))
        self.assertEqual("1", next(iter(rsp.json[next(iter(rsp.json))])))
        self.assertIn(EConsentLog.ID, rsp.json[next(iter(rsp.json))]["1"])
        self.assertTrue(
            validate_object_id(rsp.json[next(iter(rsp.json))]["1"][EConsentLog.ID])
        )

    def test_success_retrieve_empty_all_users_econsent_pdf_for_manager(self):
        econsent_id = "5e9443789911c97c0b639445"
        rsp = self.flask_client.get(
            f"{self.deployment_route}/user/{self.manager_id}/econsent/{econsent_id}/pdf",
            headers=self.headers_for_manager,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual({}, rsp.json)

    def test_success_retrieve_empty_user_econsent_pdf_for_manager(self):
        econsent_id = "5e9443789911c97c0b639447"
        rsp = self.flask_client.get(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{econsent_id}/pdf",
            headers=self.headers_for_manager,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual({}, rsp.json)

    def test_failure_retrieve_invalid_econsent_pdf_for_user(self):
        econsent_id = "5e9443789911c97c0b639445"
        self.remove_onboarding()
        rsp = self.flask_client.get(
            f"{self.deployment_route}/user/{self.user_id}/econsent/{econsent_id}/pdf",
            headers=self.headers_for_user,
        )
        self.assertEqual(404, rsp.status_code)

    def test_success_not_returning_non_consenting_consent_log(self):
        rsp = self.flask_client.post(
            f"{self.deployment_route}/user/{self.user_id2}/econsent/{self.latest_econsent_id}/sign",
            headers=self.headers_for_user2,
            json={**simple_econsent_log(), EConsentLog.CONSENT_OPTION: 0},
        )
        self.assertEqual(412, rsp.status_code)
        rsp = self.flask_client.get(
            f"{self.deployment_route}/user/{self.user_id2}/econsent/{self.latest_econsent_id}/pdf",
            headers=self.headers_for_manager,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertDictEqual({}, rsp.json)
