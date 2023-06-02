from bson import ObjectId

from extensions.authorization.models.role.role import RoleName
from extensions.authorization.router.admin_invitation_request_objects import (
    SendAdminInvitationsRequestObject,
)
from extensions.tests.authorization.IntegrationTests.invitation_tests import (
    AbstractInvitationTestCase,
)
from .test_helpers import SUPER_ADMIN_ID

TEST_EMAIL = "test@huma.com"
SAMPLE_ID = "61e0303f3547262976bd66bb"


class AdminInvitationTestCase(AbstractInvitationTestCase):
    def test_success_invite_account_manager_full_flow(self):
        response = self.send_invitation(
            role_id=RoleName.ACCOUNT_MANAGER,
            email=TEST_EMAIL,
            sender_id=SUPER_ADMIN_ID,
        )
        self.assertEqual(200, response.status_code)

        self.assertSignUpSuccessfulAs(
            RoleName.ACCOUNT_MANAGER,
            invitation_id=response.json["ids"][0],
        )

    def send_invitation(self, role_id: str, email: str, sender_id: str):
        invitation_body = {
            SendAdminInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendAdminInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendAdminInvitationsRequestObject.ROLE_ID: role_id,
            SendAdminInvitationsRequestObject.EMAILS: [email],
            SendAdminInvitationsRequestObject.ORGANIZATION_ID: SAMPLE_ID,
        }
        return self.flask_client.post(
            "/api/extensions/v1beta/admin/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(sender_id),
        )

    def assertSignUpSuccessfulAs(self, as_role: str, invitation_id: str):
        invitation = self.get_invitation(invitation_id)
        data = {
            "method": 0,
            "email": invitation["email"],
            "validationData": {"invitationCode": invitation["code"]},
            "clientId": "ctest1",
            "projectId": "ptest1",
        }
        response = self.flask_client.post("/api/auth/v1beta/signup", json=data)
        self.assertEqual(200, response.status_code)

        user = self.mongo_database.user.find_one(
            {"_id": ObjectId(response.json["uid"])}
        )
        roles = user["roles"]
        self.assertEqual(1, len(roles))
        self.assertEqual(as_role, next(iter(roles))["roleId"])
