from pathlib import Path

from bson import ObjectId

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.authorized_user import ProxyStatus
from extensions.authorization.models.user import BoardingStatus, User
from extensions.authorization.router.user_profile_request import (
    CreateHelperAgreementLogRequestObject,
    OffBoardUserRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import ReasonDetails, Reason
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    USER_1_ID_DEPLOYMENT_Y,
)
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.localization.utils import Language
from sdk.tests.auth.IntegrationTests.email_password_auth_router_tests import X_HU_LOCALE
from tools.mongodb_script.update_offboarding_reasons_localization import (
    update_offboarding_localizations,
)

VALID_USER1_ID = "5e8f0c74b50aa9656c34789b"
PROXY_USER_FOR_USER1 = "606eba3a2c94383d620b52ad"
VALID_USER2_ID = "601919b5c03550c421c075eb"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"
CALL_CENTER_ID = "602fa576c06fe59e3556142a"
INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
CALL_CENTER_ID2 = "602fa576c06fe59e3556142b"


class OffBoardUserTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
    ]
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployments_dump.json"),
        Path(__file__).parent.joinpath("fixtures/users_dump.json"),
    ]

    def setUp(self):
        super().setUp()
        self.headers_user1 = self.get_headers_for_token(VALID_USER1_ID)
        self.headers_contributor = self.get_headers_for_token(VALID_CONTRIBUTOR_ID)

        self.base_route = "/api/extensions/v1beta/user"

    def get_profile(self, user_id, headers=None) -> dict:
        rsp = self.flask_client.get(
            f"{self.base_route}/{user_id}", headers=headers or self.headers_user1
        )
        self.assertEqual(200, rsp.status_code)
        return rsp.json

    def test_success_manual_off_board_user(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/offboard"
        data_dict = {
            OffBoardUserRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED
        }
        rsp = self.flask_client.post(
            path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 200)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER1_ID}", headers=self.headers_contributor
        )
        self.assertEqual(rsp.status_code, 200)
        data = rsp.json[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED)
        self.assertEqual(data[BoardingStatus.SUBMITTER_ID], VALID_CONTRIBUTOR_ID)
        self.assertEqual(
            data[BoardingStatus.REASON_OFF_BOARDED],
            BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED,
        )

    def test_success_off_board_user_off_boards_proxy_user(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/offboard"
        data_dict = {
            OffBoardUserRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED
        }
        rsp = self.flask_client.post(
            path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 200)

        rsp = self.get_profile(VALID_USER1_ID, self.headers_contributor)
        data = rsp[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED)
        self.assertEqual(data[BoardingStatus.SUBMITTER_ID], VALID_CONTRIBUTOR_ID)

        rsp = self.get_profile(PROXY_USER_FOR_USER1, self.headers_contributor)
        data = rsp[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED)
        self.assertEqual(data[BoardingStatus.SUBMITTER_ID], VALID_CONTRIBUTOR_ID)

    def test_offboard_details_localized_properly(self):
        headers = {**self.headers_contributor, X_HU_LOCALE: Language.DE_DE}
        config_url = f"{self.base_route}/{VALID_USER1_ID}/configuration"
        config_rsp = self.flask_client.get(config_url, headers=headers)
        reasons = config_rsp.json["features"]["offBoardingReasons"]["reasons"]
        deceased_reason = reasons[1]["displayName"]
        self.assertEqual("Verstorben", deceased_reason)
        self.assertNotEqual(deceased_reason, ReasonDetails.DECEASED)

        offboard_path = f"{self.base_route}/{VALID_USER1_ID}/offboard"
        data_dict = {OffBoardUserRequestObject.DETAILS_OFF_BOARDED: deceased_reason}
        rsp = self.flask_client.post(
            offboard_path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 200)

        rsp = self.get_profile(VALID_USER1_ID, self.headers_contributor)
        data = rsp[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.DETAILS_OFF_BOARDED], deceased_reason)

    def test_offboard_details_localized_properly_after_migration(self):
        # checking existing reasons
        contributor_id = "5ff744265208ef492e895f1c"
        contributor_headers = self.get_headers_for_token(contributor_id)
        headers = {**contributor_headers, X_HU_LOCALE: Language.DE_DE}
        config_url = f"{self.base_route}/{USER_1_ID_DEPLOYMENT_Y}/configuration"
        config_rsp = self.flask_client.get(config_url, headers=headers)
        reasons = config_rsp.json["features"]["offBoardingReasons"]["reasons"]
        deceased_reason = reasons[1]["displayName"]
        # confirming reason is not localized in deployment
        self.assertEqual("Deceased", deceased_reason)

        # offboarding with not localized reason
        offboard_path = f"{self.base_route}/{USER_1_ID_DEPLOYMENT_Y}/offboard"
        data_dict = {OffBoardUserRequestObject.DETAILS_OFF_BOARDED: deceased_reason}
        rsp = self.flask_client.post(offboard_path, headers=headers, json=data_dict)
        self.assertEqual(rsp.status_code, 200)
        # confirming reason is not localized in offboarded details
        rsp = self.get_profile(USER_1_ID_DEPLOYMENT_Y, headers)
        data = rsp[User.BOARDING_STATUS]
        self.assertEqual(deceased_reason, data[BoardingStatus.DETAILS_OFF_BOARDED])

        # applying migration
        default_reasons = Reason._default_reasons()
        update_offboarding_localizations(self.mongo_database, default_reasons)

        # confirming localized properly to DE-de
        rsp = self.get_profile(USER_1_ID_DEPLOYMENT_Y, headers)
        data = rsp[User.BOARDING_STATUS]
        self.assertEqual("Verstorben", data[BoardingStatus.DETAILS_OFF_BOARDED])

    def test_success_off_board_proxy_user_on_decline_agreement(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/deployment/{DEPLOYMENT_ID}/helperagreementlog"
        # with patch.object(AuthorizationService, "off_board_user")
        not_agree = CreateHelperAgreementLogRequestObject.Status.DO_NOT_AGREE
        data = {CreateHelperAgreementLogRequestObject.STATUS: not_agree.value}

        rsp = self.flask_client.post(path, headers=self.headers_user1, json=data)
        self.assertEqual(rsp.status_code, 412)
        rsp = self.flask_client.get(
            f"{self.base_route}/{VALID_USER1_ID}", headers=self.headers_user1
        )
        self.assertEqual(rsp.status_code, 200)
        data = rsp.json[User.BOARDING_STATUS]
        self.assertEqual(data[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED)
        self.assertNotIn(BoardingStatus.SUBMITTER_ID, data)
        self.assertEqual(
            data[BoardingStatus.REASON_OFF_BOARDED],
            BoardingStatus.ReasonOffBoarded.USER_FAIL_HELPER_AGREEMENT,
        )

    def test_success_manual_off_board_user_call_center(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/offboard"
        headers = self.get_headers_for_token(CALL_CENTER_ID)
        data_dict = {
            OffBoardUserRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED
        }
        rsp = self.flask_client.post(path, headers=headers, json=data_dict)
        self.assertEqual(rsp.status_code, 200)
        user = self.get_profile(VALID_USER1_ID, headers)
        user = User.from_dict(user)
        self.assertTrue(user.boardingStatus.is_off_boarded())
        proxy_dict = self.get_profile(PROXY_USER_FOR_USER1, headers)
        proxy_status = proxy_dict["proxyStatus"]
        self.assertEqual(ProxyStatus.LINKED.value, proxy_status)

    def test_success_manual_off_board_user_call_supports_other_reason(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/offboard"
        headers = self.get_headers_for_token(CALL_CENTER_ID)
        data_dict = {OffBoardUserRequestObject.DETAILS_OFF_BOARDED: "Some Reason"}
        rsp = self.flask_client.post(path, headers=headers, json=data_dict)
        self.assertEqual(rsp.status_code, 200)
        user = self.get_profile(VALID_USER1_ID, headers)
        user = User.from_dict(user)
        self.assertTrue(user.boardingStatus.is_off_boarded())
        proxy_dict = self.get_profile(PROXY_USER_FOR_USER1, headers)
        proxy_status = proxy_dict["proxyStatus"]
        self.assertEqual(ProxyStatus.LINKED.value, proxy_status)

    def test_failure_manual_off_board_user_call_doesnt_supports_other_reason(self):
        self.mongo_database.deployment.update_one(
            {"_id": ObjectId("5ed8ae76cf99540b259a7315")},
            {
                "$set": {"features.offBoardingReasons.otherReason": False},
            },
        )
        path = f"{self.base_route}/{VALID_USER2_ID}/offboard"
        headers = self.get_headers_for_token(CALL_CENTER_ID2)
        data_dict = {OffBoardUserRequestObject.DETAILS_OFF_BOARDED: "Some Reason"}
        rsp = self.flask_client.post(path, headers=headers, json=data_dict)
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], ErrorCodes.INVALID_REQUEST)

    def test_failure_user_can_offboard_himself(self):
        path = f"{self.base_route}/{VALID_USER1_ID}/offboard"
        rsp = self.flask_client.post(path, headers=self.headers_user1)
        self.assertEqual(rsp.status_code, 403)
        proxy_dict = self.get_profile(PROXY_USER_FOR_USER1, self.headers_contributor)
        proxy_status = proxy_dict["proxyStatus"]
        self.assertEqual(ProxyStatus.LINKED.value, proxy_status)

    def test_failure_user_off_board_other_user(self):
        path = f"{self.base_route}/{VALID_USER2_ID}/offboard"
        rsp = self.flask_client.post(path, headers=self.headers_user1)
        self.assertEqual(rsp.status_code, 403)

    def test_failure_manual_off_board_un_existent_user(self):
        path = f"{self.base_route}/{INVALID_USER_ID}/offboard"
        rsp = self.flask_client.post(path, headers=self.headers_user1)
        self.assertEqual(rsp.status_code, 404)
