from pathlib import Path
from unittest.mock import patch, MagicMock

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.user import BoardingStatus, User
from extensions.authorization.router.user_profile_request import (
    OffBoardUsersRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import ReasonDetails
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.localization.utils import Language
from sdk.common.requests.request_utils import RequestContext

VALID_USER1_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER2_ID = "5e8f0c74b50aa9656c34789c"
VALID_USER_ID_DEPLOYMENT_2 = "601919b5c03550c421c075eb"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"
INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"


class OffBoardUsersTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
        ExportDeploymentComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]
    override_config = {
        "server.deployment.offBoarding": "true",
        "server.exportDeployment.enableAuth": "true",
    }

    def setUp(self):
        super().setUp()
        self.headers_user1 = self.get_headers_for_token(VALID_USER1_ID)
        self.headers_contributor = self.get_headers_for_token(VALID_CONTRIBUTOR_ID)

        self.user_route = "/api/extensions/v1beta/user"
        self.offboard_route = "/api/extensions/v1beta/user/offboard"

    def test_success_offboard_users(self):
        user_ids = [VALID_USER1_ID, VALID_USER2_ID]
        data_dict = {
            OffBoardUsersRequestObject.USER_IDS: user_ids,
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED,
        }
        rsp = self.flask_client.post(
            self.offboard_route, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 200)
        for user_id in user_ids:
            rsp = self.flask_client.get(
                f"{self.user_route}/{user_id}", headers=self.headers_contributor
            )
            self.assertEqual(rsp.status_code, 200)
            data = rsp.json[User.BOARDING_STATUS]
            self.assertEqual(
                data[BoardingStatus.STATUS], BoardingStatus.Status.OFF_BOARDED
            )
            self.assertEqual(data[BoardingStatus.SUBMITTER_ID], VALID_CONTRIBUTOR_ID)
            self.assertEqual(
                data[BoardingStatus.REASON_OFF_BOARDED],
                BoardingStatus.ReasonOffBoarded.USER_MANUAL_OFF_BOARDED,
            )

    def test_failure_user_offboard_other_user(self):
        data_dict = {
            OffBoardUsersRequestObject.USER_IDS: [VALID_USER2_ID],
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED,
        }
        rsp = self.flask_client.post(
            self.offboard_route, headers=self.headers_user1, json=data_dict
        )
        self.assertEqual(rsp.status_code, 403)

    def test_failure_offboard_inexistent_user(self):
        data_dict = {
            OffBoardUsersRequestObject.USER_IDS: [INVALID_USER_ID],
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED,
        }
        rsp = self.flask_client.post(
            self.offboard_route, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 404)

    def test_failure_offboard_users_from_other_deployment(self):
        user_ids = [VALID_USER_ID_DEPLOYMENT_2]
        data_dict = {
            OffBoardUsersRequestObject.USER_IDS: user_ids,
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED,
        }
        rsp = self.flask_client.post(
            self.offboard_route, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 403)

    def test_offboard_users_localization(self):
        user_ids = [VALID_USER1_ID]
        headers = {
            **self.headers_contributor,
            RequestContext.X_HU_LOCALE: Language.DE_DE,
        }
        data_dict = {
            OffBoardUsersRequestObject.USER_IDS: user_ids,
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: "Genesen",
        }
        rsp = self.flask_client.post(
            self.offboard_route, headers=headers, json=data_dict
        )
        self.assertEqual(rsp.status_code, 200)

        headers = {**self.headers_contributor, RequestContext.X_HU_LOCALE: Language.EN}
        rsp = self.flask_client.get(
            f"{self.user_route}/{VALID_USER1_ID}", headers=headers
        )
        self.assertEqual(rsp.status_code, 200)
        data = rsp.json[User.BOARDING_STATUS]
        self.assertEqual("Recovered", data[BoardingStatus.DETAILS_OFF_BOARDED])

    @patch("extensions.export_deployment.tasks.run_export.apply_async", MagicMock())
    def test_success_access_after_offboarding_user(self):
        user_ids = [VALID_USER1_ID]
        # Extract when on-boarded
        data_dict = {"userIds": user_ids}
        path = f"/api/extensions/v1beta/export/user/{VALID_USER1_ID}/task"
        rsp = self.flask_client.post(
            path,
            headers=self.headers_user1,
            json=data_dict,
        )
        self.assertEqual(200, rsp.status_code)
        export_process_id = rsp.json["exportProcessId"]

        # Make user off-boarded
        data_dict = {
            OffBoardUsersRequestObject.USER_IDS: user_ids,
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED,
        }
        rsp = self.flask_client.post(
            self.offboard_route, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(200, rsp.status_code)

        # Check extract status when off-boarded
        path = f"/api/extensions/v1beta/export/user/{VALID_USER1_ID}/task/{export_process_id}"
        rsp = self.flask_client.get(
            path,
            headers=self.headers_user1,
            json={},
        )
        self.assertEqual(200, rsp.status_code)
