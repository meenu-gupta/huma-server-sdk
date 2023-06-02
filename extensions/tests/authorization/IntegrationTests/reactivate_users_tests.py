from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.router.user_profile_request import (
    OffBoardUsersRequestObject,
    ReactivateUsersRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.deployment.models.deployment import ReasonDetails
from extensions.exceptions import UserErrorCodes
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent

VALID_USER1_ID = "5e8f0c74b50aa9656c34789b"
VALID_USER2_ID = "5e8f0c74b50aa9656c34789c"
WITHDRAWN_ECONSENT_USER_ID = "62569f29e427af0b5c12779a"
VALID_USER_ID_DEPLOYMENT_2 = "601919b5c03550c421c075eb"
VALID_CONTRIBUTOR_ID = "60071f359e7e44330f732037"
INVALID_USER_ID = "5e8f0c74b50aa9656c34789a"


class ReactivateUsersTests(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]

    def setUp(self):
        super().setUp()
        self.headers_user1 = self.get_headers_for_token(VALID_USER1_ID)
        self.headers_contributor = self.get_headers_for_token(VALID_CONTRIBUTOR_ID)

        self.user_route = "/api/extensions/v1beta/user"
        self.offboard_route = "/api/extensions/v1beta/user/offboard"
        self.reactivate_route = "/api/extensions/v1beta/user/reactivate"

    def test_success_reactivate_users(self):
        user_ids = [VALID_USER1_ID, VALID_USER2_ID]
        offboard_data_dict = {
            OffBoardUsersRequestObject.USER_IDS: user_ids,
            OffBoardUsersRequestObject.DETAILS_OFF_BOARDED: ReasonDetails.RECOVERED,
        }
        rsp = self.flask_client.post(
            self.offboard_route,
            headers=self.headers_contributor,
            json=offboard_data_dict,
        )
        self.assertEqual(rsp.status_code, 200)

        reactivate_data_dict = {
            ReactivateUsersRequestObject.USER_IDS: user_ids,
        }
        rsp = self.flask_client.post(
            self.reactivate_route,
            headers=self.headers_contributor,
            json=reactivate_data_dict,
        )
        self.assertEqual(rsp.status_code, 200)

    def test_failure_reactivate_inexistent_user(self):
        path = self.reactivate_route
        data_dict = {
            ReactivateUsersRequestObject.USER_IDS: [INVALID_USER_ID],
        }
        rsp = self.flask_client.post(
            path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 404)

    def test_failure_reactivate_active_user(self):
        path = self.reactivate_route
        data_dict = {
            ReactivateUsersRequestObject.USER_IDS: [VALID_USER1_ID],
        }
        rsp = self.flask_client.post(
            path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 400)

    def test_failure_reactivate_active_user_withdrawn_econsent(self):
        path = self.reactivate_route
        data_dict = {
            ReactivateUsersRequestObject.USER_IDS: [WITHDRAWN_ECONSENT_USER_ID],
        }
        rsp = self.flask_client.post(
            path, headers=self.headers_contributor, json=data_dict
        )
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.json["code"], UserErrorCodes.WITHDRAWN_ECONSENT)
