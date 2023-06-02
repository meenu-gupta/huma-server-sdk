from datetime import datetime
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

import jwt
from bson import ObjectId
from freezegun import freeze_time
from jwt import PyJWS

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.middleware import AuthorizationMiddleware
from extensions.authorization.models.invitation import Invitation, InvitationType
from extensions.authorization.models.mongo_invitation import MongoInvitation
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import RoleName
from extensions.authorization.models.user import RoleAssignment, User
from extensions.authorization.router.invitation_request_objects import (
    SendInvitationsRequestObject,
    ResendInvitationsRequestObject,
    GetInvitationLinkRequestObject,
    RetrieveInvitationsRequestObject,
    ResendInvitationsListRequestObject,
    DeleteInvitationsListRequestObject,
)
from extensions.authorization.router.invitation_response_objects import (
    SendInvitationsResponseObject,
    GetInvitationLinkResponseObject,
    RetrieveInvitationsResponseObject,
    InvitationResponseModel,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveProxyInvitationsResponseObject,
)
from extensions.common.sort import SortField
from extensions.tests.authorization.IntegrationTests.abstract_permission_test_case import (
    AbstractPermissionTestCase,
)
from extensions.tests.authorization.IntegrationTests.test_helpers import (
    get_invitation_sign_up_data,
    DEPLOYMENT_ID,
    ORGANIZATION_ID,
    ACCESS_CONTROLLER_ID,
    USER_WITHOUT_ROLE_EMAIL,
    CONTRIBUTOR_1_ID_DEPLOYMENT_X,
    DEPLOYMENT_2_ID,
    USER_2_ID_DEPLOYMENT_X,
    MANAGER_2_ID_DEPLOYMENT_X,
    MANAGER_1_ID_DEPLOYMENT_X,
    USER_1_ID_DEPLOYMENT_X,
    ACCOUNT_MANAGER_ID,
    ORG_OWNER_ID,
    ORG_EDITOR_ID,
    SUPPORT_ID,
    ORGANIZATION_ADMINISTRATOR_ID,
    DEPLOYMENT_ADMINISTRATOR_ID,
    MULTI_DEPLOYMENT_ADMINISTRATOR_ID,
    SUPER_ADMIN_ID,
    SUPERVISOR_ID,
    CLINICIAN_ID,
    HUMA_SUPPORT_ID,
)
from sdk.auth.model.auth_user import AuthUser
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.common.utils.token.jwt.jwt import USER_CLAIMS_KEY
from sdk.common.utils.validators import remove_none_values

VALID_INVITATION_CODE = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTYwNzAwMjQsIm5iZiI6MTYxNjA3MDAyNCwianRpIjoiYjliMDRiYzQtNmFiZi00MzkwLWI0MjUtYTM1YTc1NjgyNWQ4IiwiaWRlbnRpdHkiOiJ1c2VyMUBleGFtcGxlLmNvbSIsInR5cGUiOiJpbnZpdGF0aW9uIn0.6M22glMJAavCoeHGf8CEDOWyn9SBNyITxQot7PpaHZo"
VALID_INVITATION_EMAIL = "user1@example.com"
PATIENT_ID = "601919b5c03550c421c075eb"
PATIENT_NAME = "Thomas"
TEST_EMAIL = "test@huma.com"
UNIVERSAL_CODE_EMAIL = "universal@huma.com"
UNIVERSAL_CODE_EMAIL_2 = "universal2@huma.com"
EXISTING_INVITATION_ID = "605345882f7d4c18ef9e6dbb"
EXISTING_UNIVERSAL_INVITATION_ID = "620628918975395487e5814b"
INVITATION_COLLECTION = "invitation"
NOT_EXISTING_INVITATION_ID = "605345882f7d4c18ef9e6dab"
ORG_ROLE_USER_IDS = {
    RoleName.SUPPORT: SUPPORT_ID,
    RoleName.CLINICIAN: CLINICIAN_ID,
    RoleName.SUPERVISOR: SUPERVISOR_ID,
}


class AbstractInvitationTestCase(AbstractPermissionTestCase):
    def get_invitation(self, invitation_id: str = None, invitation_email: str = None):
        query = remove_none_values(
            {
                Invitation.ID_: ObjectId(invitation_id) if invitation_id else None,
                Invitation.EMAIL: invitation_email,
            }
        )
        return self.mongo_database[INVITATION_COLLECTION].find_one(query)

    def request_invitations_list(
        self,
        requester: str,
        role_type: str,
        update_body: dict = None,
        extra_headers: dict = None,
        version: str = "v1beta",
        invitation_type: InvitationType = None,
        sort_fields: list[dict] = None,
        email: str = None,
    ):
        request_data = {
            RetrieveInvitationsRequestObject.ROLE_TYPE: role_type,
            RetrieveInvitationsRequestObject.CLIENT_ID: "ctest1",
            RetrieveInvitationsRequestObject.PROJECT_ID: "ptest1",
            RetrieveInvitationsRequestObject.SKIP: 0,
            RetrieveInvitationsRequestObject.LIMIT: 10,
        }
        if sort_fields:
            request_data[RetrieveInvitationsRequestObject.SORT_FIELDS] = sort_fields
        if invitation_type:
            request_data[
                RetrieveInvitationsRequestObject.INVITATION_TYPE
            ] = invitation_type
        if email:
            request_data[RetrieveInvitationsRequestObject.EMAIL] = email
        if update_body:
            request_data.update(update_body)
        headers = self.get_headers_for_token(requester)
        if extra_headers:
            headers.update(extra_headers)
        return self.flask_client.post(
            f"/api/extensions/{version}/deployment/invitations",
            json=request_data,
            headers=headers,
        )

    def resend_invitation(
        self, test_email, mocked_send_email, language: str = Language.EN
    ):
        mocked_send_email.assert_called_once()
        code = mocked_send_email.call_args.args[3]
        mocked_send_email.reset_mock()

        data = {
            ResendInvitationsRequestObject.EMAIL: test_email,
            ResendInvitationsRequestObject.INVITATION_CODE: code,
            ResendInvitationsRequestObject.CLIENT_ID: "ctest1",
            ResendInvitationsRequestObject.PROJECT_ID: "ptest1",
            ResendInvitationsRequestObject.LANGUAGE: language,
        }

        return self.flask_client.post(
            "/api/extensions/v1beta/deployment/resend-invitation",
            json=data,
        )

    def resend_invitation_list(
        self, test_email_list, mocked_send_email, language: str = Language.EN
    ):
        mocked_send_email.assert_called_once()
        code = mocked_send_email.call_args.args[3]
        mocked_send_email.reset_mock()

        data = {
            ResendInvitationsListRequestObject.INVITATIONS_LIST: [
                {
                    ResendInvitationsListRequestObject.InvitationItem.EMAIL: test_email,
                    ResendInvitationsListRequestObject.InvitationItem.INVITATION_CODE: code,
                }
                for test_email in test_email_list
            ],
            ResendInvitationsListRequestObject.CLIENT_ID: "ctest1",
            ResendInvitationsListRequestObject.PROJECT_ID: "ptest1",
            ResendInvitationsListRequestObject.LANGUAGE: language,
        }

        return self.flask_client.post(
            "/api/extensions/v1beta/deployment/resend-invitation-list",
            json=data,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )


class InvitationTestCase(AbstractInvitationTestCase):
    @patch.object(PyJWS, "_verify_signature")
    def test_sign_up_with_invitation(self, _):
        self.assertIsNotNone(self.get_invitation(EXISTING_INVITATION_ID))
        user_data = get_invitation_sign_up_data(
            email=VALID_INVITATION_EMAIL,
            name="user1",
            invitation_code=VALID_INVITATION_CODE,
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["authuser"].find_one({"_id": ObjectId(user_id)})
        self.assertTrue(db_user[AuthUser.EMAIL_VERIFIED])
        self.assertIsNone(self.get_invitation(EXISTING_INVITATION_ID))

    def test_send_invitation_existing_user_upper_case(self):
        existing_email = "test@test.com"
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.DEPLOYMENT_STAFF,
            SendInvitationsRequestObject.EMAILS: [existing_email.upper()],
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )

        self.assertIn(
            existing_email.upper(),
            rsp.json[SendInvitationsResponseObject.ALREADY_SIGNED_UP_EMAILS],
        )

    @patch.object(EmailInvitationAdapter, "send_role_update_email")
    def test_send_invitation_existing_user_without_role(self, mocked_email):
        invitation_body = {
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.ACCESS_CONTROLLER,
            SendInvitationsRequestObject.EMAILS: [USER_WITHOUT_ROLE_EMAIL],
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        mocked_email.assert_called_once()

    def test_invitation_sign_up_upper_case(self):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.DEPLOYMENT_STAFF,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }
        self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )
        invitation = self.get_invitation(invitation_email=TEST_EMAIL)
        invitation_code = invitation[Invitation.CODE]

        user_data = get_invitation_sign_up_data(
            email=TEST_EMAIL.upper(), name="user1", invitation_code=invitation_code
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        self.assertIsNotNone(rsp.json["uid"])

        # verify invitation create date time in jwt
        decoded_code = jwt.decode(invitation_code, verify=False)
        self.assertIn(Invitation.CREATE_DATE_TIME, decoded_code[USER_CLAIMS_KEY])

    def test_send_invitation_organization_staff_access_controller(self):
        roles_to_test = (
            RoleName.ACCESS_CONTROLLER,
            RoleName.ORGANIZATION_STAFF,
        )
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
            )
            self.assertEqual(rsp.status_code, 200, role)
            self.assertTrue(rsp.json["ok"])

    def test_send_invitation_one_deployment_call_center_or_deployment_staff(self):
        roles_to_test = [
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_send_invitations_by_org_administrator(self):
        roles_to_test = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_send_invitations_by_dep_administrator(self):
        roles_to_test = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
            RoleName.USER,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(DEPLOYMENT_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 403)

            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(DEPLOYMENT_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_failure_invitation_by_administrator(self):
        not_allowed_roles = [RoleName.ORGANIZATION_STAFF, RoleName.ACCESS_CONTROLLER]
        for role in not_allowed_roles:
            invitation_body = {
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 403)

    def test_success_send_invitation_common_roles_by_super_admins(self):
        allowed_super_admins = [
            HUMA_SUPPORT_ID,
            SUPER_ADMIN_ID,
            ORG_EDITOR_ID,
            ORG_OWNER_ID,
        ]
        test_roles = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        for staff in allowed_super_admins:
            for role in test_roles:
                invitation_body = {
                    SendInvitationsRequestObject.DEPLOYMENT_IDS: [
                        DEPLOYMENT_ID,
                    ],
                    SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                    SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                    SendInvitationsRequestObject.ROLE_ID: role,
                    SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
                }
                rsp = self.flask_client.post(
                    "/api/extensions/v1beta/deployment/send-invitation",
                    json=invitation_body,
                    headers=self.get_headers_for_token(staff),
                )
                self.assertEqual(rsp.status_code, 200)
                self.assertTrue(rsp.json["ok"])

    def test_failure_send_invitation_common_roles_by_super_admins(self):
        not_allowed_super_admins = [ACCOUNT_MANAGER_ID]
        test_roles = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        for staff in not_allowed_super_admins:
            for role in test_roles:
                invitation_body = {
                    SendInvitationsRequestObject.DEPLOYMENT_IDS: [
                        DEPLOYMENT_ID,
                    ],
                    SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                    SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                    SendInvitationsRequestObject.ROLE_ID: role,
                    SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
                }
                rsp = self.flask_client.post(
                    "/api/extensions/v1beta/deployment/send-invitation",
                    json=invitation_body,
                    headers=self.get_headers_for_token(staff),
                )
                self.assertEqual(rsp.status_code, 403)

    def test_send_invitation_multiple_deployments_call_center_or_deployment_staff(self):
        roles_to_test = [
            RoleName.DEPLOYMENT_STAFF,
            RoleName.CALL_CENTER,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [
                    DEPLOYMENT_ID,
                    DEPLOYMENT_2_ID,
                ],
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_send_invitation_multiple_deployments_org_administrator(self):
        roles_to_test = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [
                    DEPLOYMENT_ID,
                    DEPLOYMENT_2_ID,
                ],
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_send_invitation_multiple_deployments_dep_administrator(self):
        roles_to_test = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [
                    DEPLOYMENT_ID,
                    DEPLOYMENT_2_ID,
                ],
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(MULTI_DEPLOYMENT_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_failure_send_invitation_multiple_deployments_dep_administrator(self):
        roles_to_test = [
            RoleName.ADMINISTRATOR,
            RoleName.CLINICIAN,
            RoleName.SUPERVISOR,
            RoleName.SUPPORT,
        ]
        for role in roles_to_test:
            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [
                    DEPLOYMENT_ID,
                    DEPLOYMENT_2_ID,
                ],
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(DEPLOYMENT_ADMINISTRATOR_ID),
            )
            self.assertEqual(rsp.status_code, 403)

    def test_failure_send_invitation_by_common_roles_with_no_invite_permission(self):
        sample_roles = inject.instance(DefaultRoles)
        for role in sample_roles:
            invitation_body = {
                SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: role,
                SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
            }
            for test_role in ORG_ROLE_USER_IDS.keys():
                rsp = self.flask_client.post(
                    "/api/extensions/v1beta/deployment/send-invitation",
                    json=invitation_body,
                    headers=self.get_headers_for_token(
                        ORG_ROLE_USER_IDS.get(test_role)
                    ),
                )
                self.assertEqual(rsp.status_code, 403, role)

    @freeze_time("2012-01-01")
    def test_send_invitation_custom_expiration(self):
        expirations_to_test = {
            "P1W": datetime(2012, 1, 8, 0, 0),
            "P1D": datetime(2012, 1, 2, 0, 0),
            "P3D": datetime(2012, 1, 4, 0, 0),
        }
        for expiration, target_dt in expirations_to_test.items():
            invitation_body = {
                SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
                SendInvitationsRequestObject.CLIENT_ID: "ctest1",
                SendInvitationsRequestObject.PROJECT_ID: "ptest1",
                SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
                SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
                SendInvitationsRequestObject.EXPIRES_IN: expiration,
            }
            res = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
            )
            self.assertEqual(200, res.status_code)
            invitation_id = res.json["ids"][0]
            invitation = self.get_invitation(invitation_id)
            self.assertEqual(target_dt, invitation[MongoInvitation.EXPIRES_AT])

    @patch.object(PyJWS, "_verify_signature")
    def test_sign_up_with_invitation_deployment_staff(self, mocked_verify):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.DEPLOYMENT_STAFF,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }
        self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )

        invitation = self.get_invitation(invitation_email=TEST_EMAIL)
        user_data = get_invitation_sign_up_data(
            email=TEST_EMAIL, name="user1", invitation_code=invitation["code"]
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})
        role = db_user[User.ROLES][-1]
        self.assertEqual(RoleName.DEPLOYMENT_STAFF, role[RoleAssignment.ROLE_ID])
        self.assertEqual(f"deployment/{DEPLOYMENT_ID}", role[RoleAssignment.RESOURCE])

    @patch.object(PyJWS, "_verify_signature")
    def test_sign_up_with_invitation_user(self, mocked_verify):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }
        self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )

        invitation = self.get_invitation(invitation_email=TEST_EMAIL)
        user_data = get_invitation_sign_up_data(
            email=TEST_EMAIL, name="user1", invitation_code=invitation["code"]
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})
        role = db_user[User.ROLES][-1]
        self.assertEqual(RoleName.USER, role[RoleAssignment.ROLE_ID])
        self.assertEqual(f"deployment/{DEPLOYMENT_ID}", role[RoleAssignment.RESOURCE])

    @patch.object(PyJWS, "_verify_signature")
    def test_fail_sign_up_with_invitation_wrong_email(self, _):
        user_data = get_invitation_sign_up_data(
            email="somerandom@mail.com",
            name="user1",
            invitation_code=VALID_INVITATION_CODE,
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(ErrorCodes.INVALID_REQUEST, rsp.json["code"])

    @patch.object(EmailInvitationAdapter, "send_user_invitation_email")
    def test_resend_invitation(self, mocked_send_email):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }

        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        resend_rsp = self.resend_invitation(TEST_EMAIL, mocked_send_email)
        self.assertEqual(200, resend_rsp.status_code)

        # confirming resend finds new invitation with old code
        resend_rsp = self.resend_invitation(TEST_EMAIL, mocked_send_email)
        self.assertEqual(resend_rsp.status_code, 200)
        email = mocked_send_email.call_args.args[0]
        self.assertEqual(email, TEST_EMAIL)

    @patch.object(EmailInvitationAdapter, "send_user_invitation_email")
    def test_resend_invitation_list(self, mocked_send_email):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }

        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)

        resend_rsp = self.resend_invitation_list([TEST_EMAIL], mocked_send_email)
        self.assertEqual(200, resend_rsp.status_code)

        # confirming resend finds new invitation with old code
        resend_rsp = self.resend_invitation_list([TEST_EMAIL], mocked_send_email)
        self.assertEqual(resend_rsp.status_code, 200)
        email = mocked_send_email.call_args.args[0]
        self.assertEqual(email, TEST_EMAIL)

    def test_send_invitation_as_admin_portal_roles(self):
        users_to_test = [ACCOUNT_MANAGER_ID, ORG_OWNER_ID, ORG_EDITOR_ID]
        for user_id in users_to_test:
            invitation_data = {
                GetInvitationLinkRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
                GetInvitationLinkRequestObject.EXPIRES_IN: "P1Y",
                GetInvitationLinkRequestObject.CLIENT_ID: "ctest1",
                GetInvitationLinkRequestObject.PROJECT_ID: "ptest1",
                GetInvitationLinkRequestObject.ROLE_ID: RoleName.USER,
                GetInvitationLinkRequestObject.RETRIEVE_SHORTENED: False,
            }
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/invitation-link",
                json=invitation_data,
                headers=self.get_headers_for_token(user_id),
            )
            self.assertEqual(200, rsp.status_code)
        invitations = [i for i in self.mongo_database["invitation"].find()]
        self.assertEqual(ObjectId(SUPER_ADMIN_ID), invitations[0][Invitation.SENDER_ID])

    def test_generate_universal_invitation_and_signup(self):
        invitation_data = {
            GetInvitationLinkRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            GetInvitationLinkRequestObject.EXPIRES_IN: "P1Y",
            GetInvitationLinkRequestObject.CLIENT_ID: "ctest1",
            GetInvitationLinkRequestObject.PROJECT_ID: "ptest1",
            GetInvitationLinkRequestObject.ROLE_ID: RoleName.USER,
            GetInvitationLinkRequestObject.RETRIEVE_SHORTENED: False,
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/invitation-link",
            json=invitation_data,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        link = rsp.json[GetInvitationLinkResponseObject.LINK]
        parsed_link = urlparse(link)
        parsed_query = parse_qs(parsed_link.query)
        code = parsed_query.get(GetInvitationLinkResponseObject.INVITATION_CODE)[0]

        invitations_rsp = self.request_invitations_list(
            CONTRIBUTOR_1_ID_DEPLOYMENT_X, RoleName.USER, version="v1"
        )
        invitations = invitations_rsp.json[
            RetrieveInvitationsResponseObject.INVITATIONS
        ]
        self.assertEqual(2, len(invitations))
        self.assertNotIn(InvitationResponseModel.INVITATION_LINK, invitations[1])
        self.assertEqual(link, invitations[0][InvitationResponseModel.INVITATION_LINK])

        # first user signed up
        user_data = get_invitation_sign_up_data(
            email=UNIVERSAL_CODE_EMAIL, name="user1", invitation_code=code
        )
        signup_rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        self.assertEqual(200, signup_rsp.status_code)
        user_id = signup_rsp.json.get("uid")
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["authuser"].find_one({"_id": ObjectId(user_id)})
        self.assertFalse(db_user[AuthUser.EMAIL_VERIFIED])

        # second user signed up with same code
        user_data = get_invitation_sign_up_data(
            email=UNIVERSAL_CODE_EMAIL_2, name="user2", invitation_code=code
        )
        signup_rsp_2 = self.flask_client.post(
            f"{self.auth_route}/signup", json=user_data
        )
        self.assertEqual(200, signup_rsp_2.status_code)

    def test_generate_universal_invitation_and_signup_with_shortened_invitation_code(
        self,
    ):
        invitation_data = {
            GetInvitationLinkRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
            GetInvitationLinkRequestObject.EXPIRES_IN: "P1Y",
            GetInvitationLinkRequestObject.CLIENT_ID: "ctest1",
            GetInvitationLinkRequestObject.PROJECT_ID: "ptest1",
            GetInvitationLinkRequestObject.ROLE_ID: RoleName.USER,
            GetInvitationLinkRequestObject.RETRIEVE_SHORTENED: True,
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/invitation-link",
            json=invitation_data,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        link = rsp.json[GetInvitationLinkResponseObject.LINK]
        parsed_link = urlparse(link)
        parsed_query = parse_qs(parsed_link.query)
        code = parsed_query.get(GetInvitationLinkResponseObject.SHORTENED_CODE)[0]

        # first user signed up
        user_data = get_invitation_sign_up_data(
            email=UNIVERSAL_CODE_EMAIL, name="user1", shortened_invitation_code=code
        )
        signup_rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        self.assertEqual(200, signup_rsp.status_code)
        user_id = signup_rsp.json.get("uid")
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["authuser"].find_one({"_id": ObjectId(user_id)})
        self.assertFalse(db_user[AuthUser.EMAIL_VERIFIED])

        # second user signed up with same code
        user_data = get_invitation_sign_up_data(
            email=UNIVERSAL_CODE_EMAIL_2, name="user2", shortened_invitation_code=code
        )
        signup_rsp_2 = self.flask_client.post(
            f"{self.auth_route}/signup", json=user_data
        )
        self.assertEqual(200, signup_rsp_2.status_code)

    def test_filter_invitation_by_type(self):
        invitation_types = [
            InvitationType.PERSONAL.value,
            InvitationType.UNIVERSAL.value,
        ]
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        for invitation_type in invitation_types:
            rsp = self.request_invitations_list(
                MANAGER_1_ID_DEPLOYMENT_X,
                role_type,
                version="v1",
                invitation_type=invitation_type,
            )
            self.assertEqual(200, rsp.status_code)
            invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
            self.assertEqual(1, len(invitations))
            self.assertEqual(
                "test hey", invitations[0][InvitationResponseModel.INVITED_BY]
            )

    def test_sorting_for_invitations(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        dts = [
            "2031-03-21T20:23:08.136000Z",
            "2031-02-21T20:23:08.136000Z",
            "2031-01-21T20:23:08.136000Z",
        ]
        direction_res = {
            SortField.Direction.DESC.value: dts,
            SortField.Direction.ASC.value: dts[::-1],
        }

        for direction, expected_res in direction_res.items():
            rsp = self.request_invitations_list(
                MANAGER_1_ID_DEPLOYMENT_X,
                role_type,
                version="v1",
                sort_fields=[
                    {
                        SortField.FIELD: f"{Invitation.CREATE_DATE_TIME}",
                        SortField.DIRECTION: direction,
                    }
                ],
            )
            self.assertEqual(200, rsp.status_code)
            invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
            if invitations := [i["createDateTime"] for i in invitations]:
                self.assertEqual(expected_res, invitations)

        # default sorting should be descending
        rsp = self.request_invitations_list(
            MANAGER_1_ID_DEPLOYMENT_X, role_type, version="v1"
        )
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(
            direction_res[SortField.Direction.DESC.value],
            [i["createDateTime"] for i in invitations],
        )

    def test_search_pending_invitation_with_email(self):
        email = "user1@example.com"
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        rsp = self.request_invitations_list(
            MANAGER_1_ID_DEPLOYMENT_X, role_type, version="v1", email=email
        )
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(1, len(invitations))
        self.assertEqual(email, invitations[0][Invitation.EMAIL])

    def test_generate_universal_invitation_valid_for_user_only(self):
        default_roles = inject.instance(DefaultRoles)
        for role in default_roles:
            invitation_data = {
                GetInvitationLinkRequestObject.DEPLOYMENT_ID: DEPLOYMENT_ID,
                GetInvitationLinkRequestObject.EXPIRES_IN: "P1Y",
                GetInvitationLinkRequestObject.CLIENT_ID: "ctest1",
                GetInvitationLinkRequestObject.PROJECT_ID: "ptest1",
                GetInvitationLinkRequestObject.ROLE_ID: role,
                GetInvitationLinkRequestObject.RETRIEVE_SHORTENED: False,
            }

            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/invitation-link",
                json=invitation_data,
                headers=self.get_headers_for_token(MANAGER_2_ID_DEPLOYMENT_X),
            )
            if role == RoleName.USER:
                self.assertEqual(200, rsp.status_code)
            else:
                self.assertEqual(400, rsp.status_code)
                self.assertEqual(ErrorCodes.INVALID_ROLE_ID, rsp.json["code"])

            invitations = [i for i in self.mongo_database["invitation"].find()]
            self.assertEqual(
                ObjectId(SUPER_ADMIN_ID), invitations[0][Invitation.SENDER_ID]
            )

    def test_retrieve_invitations__deployment_role_returns_deployment_invitations(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        rsp = self.request_invitations_list(MANAGER_1_ID_DEPLOYMENT_X, role_type)
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(3, len(invitations))
        for invitation in invitations:
            role = invitation.get(Invitation.ROLES)[0].get(RoleAssignment.ROLE_ID)
            is_custom = ObjectId.is_valid(role)
            is_deployment_manager = role in DefaultRoles().deployment_managers
            self.assertTrue(is_custom or is_deployment_manager)

    def test_retrieve_invitations_v1(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        rsp = self.request_invitations_list(
            MANAGER_1_ID_DEPLOYMENT_X, role_type, version="v1"
        )
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(3, len(invitations))
        self.assertEqual(3, rsp.json["filtered"])
        self.assertEqual(3, rsp.json["total"])

        email_search = {RetrieveInvitationsRequestObject.EMAIL: "user1"}
        rsp = self.request_invitations_list(
            MANAGER_1_ID_DEPLOYMENT_X,
            role_type,
            update_body=email_search,
            version="v1",
        )
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(1, len(invitations))
        self.assertEqual(1, rsp.json["filtered"])
        self.assertEqual(3, rsp.json["total"])

    def test_retrieve_invitations__org_role_returns_all_org_invitations(self):
        """
        Tests that all org roles are returned when organization id is provided in headers
        """
        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        extra_headers = {
            AuthorizationMiddleware.ORGANIZATION_HEADER_KEY: ORGANIZATION_ID
        }
        rsp = self.request_invitations_list(
            ACCESS_CONTROLLER_ID, role_type, extra_headers
        )
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(2, len(invitations))
        for invitation in invitations:
            role = invitation.get(Invitation.ROLES)[0].get(RoleAssignment.ROLE_ID)
            self.assertIn(role, DefaultRoles().organization)

    def test_retrieve_invitations__org_role_returns_multi_deployment_roles_invitations(
        self,
    ):
        """
        Tests that only multi-deployment roles are returned when both org
        and deployment ids are provided in headers
        """

        role_type = RetrieveInvitationsRequestObject.RoleType.MANAGER.value
        extra_headers = {
            AuthorizationMiddleware.ORGANIZATION_HEADER_KEY: ORGANIZATION_ID,
            AuthorizationMiddleware.DEPLOYMENT_HEADER_KEY: DEPLOYMENT_ID,
        }
        rsp = self.request_invitations_list(
            ACCESS_CONTROLLER_ID, role_type, extra_headers=extra_headers
        )
        self.assertEqual(200, rsp.status_code)
        invitations = rsp.json.get(RetrieveInvitationsResponseObject.INVITATIONS)
        self.assertEqual(1, len(invitations))
        for invitation in invitations:
            roles = invitation.get(Invitation.ROLES)
            self.assertIn(
                roles[0].get(RoleAssignment.ROLE_ID),
                RoleName.multi_deployment_roles(),
            )

    def test_retrieve_invitations__user_role_forbidden(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.USER.value
        rsp = self.request_invitations_list(USER_1_ID_DEPLOYMENT_X, role_type)
        self.assertEqual(403, rsp.status_code)

    def test_retrieve_invitations__org_role_allowed_user_invitations(self):
        role_type = RetrieveInvitationsRequestObject.RoleType.USER.value
        rsp = self.request_invitations_list(ACCESS_CONTROLLER_ID, role_type)
        self.assertEqual(200, rsp.status_code)

    def test_invite_custom_role(self):
        custom_role_id = "5e8eeae1b707216625ca4202"
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: custom_role_id,
            SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.json["ok"])

    def test_invite_org_custom_role_by_org_administrator(self):
        custom_role_id = "6151051575fee50d15298adb"
        invitation_body = {
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: custom_role_id,
            SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
        }

        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ORGANIZATION_ADMINISTRATOR_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.json["ok"])

    def test_failure_invite_org_custom_role_by_dep_administrator(self):
        custom_role_id = "6151051575fee50d15298adb"
        invitation_body = {
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: custom_role_id,
            SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
        }

        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(DEPLOYMENT_ADMINISTRATOR_ID),
        )
        self.assertEqual(rsp.status_code, 403)

    def test_invite_dep_custom_role_by_org_and_deployment_administrators(self):
        custom_role_id = "5e8eeae1b707216625ca4202"
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: custom_role_id,
            SendInvitationsRequestObject.EMAILS: ["some_email@mail.com"],
        }
        for role_id in [ORGANIZATION_ADMINISTRATOR_ID, DEPLOYMENT_ADMINISTRATOR_ID]:
            rsp = self.flask_client.post(
                "/api/extensions/v1beta/deployment/send-invitation",
                json=invitation_body,
                headers=self.get_headers_for_token(role_id),
            )
            self.assertEqual(rsp.status_code, 200)
            self.assertTrue(rsp.json["ok"])

    def test_delete_invitation(self):
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation/{EXISTING_INVITATION_ID}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(204, rsp.status_code)

    def test_delete_list_invitation(self):
        body = {
            DeleteInvitationsListRequestObject.INVITATION_ID_LIST: [
                EXISTING_INVITATION_ID
            ]
        }
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation",
            json=body,
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, rsp.json["deletedInvitations"])

    def test_delete_list_invitation_universal(self):
        body = {
            DeleteInvitationsListRequestObject.INVITATION_ID_LIST: [
                EXISTING_UNIVERSAL_INVITATION_ID
            ],
            DeleteInvitationsListRequestObject.INVITATION_TYPE: "UNIVERSAL",
        }
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation",
            json=body,
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, rsp.json["deletedInvitations"])

    def test_delete_list_invitation_universal_type_mismatch(self):
        body = {
            DeleteInvitationsListRequestObject.INVITATION_ID_LIST: [
                EXISTING_UNIVERSAL_INVITATION_ID,
                EXISTING_INVITATION_ID,
            ],
            DeleteInvitationsListRequestObject.INVITATION_TYPE: "PERSONAL",
        }
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation",
            json=body,
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(404, rsp.status_code)

    def test_delete_list_invitation_not_found(self):
        body = {
            DeleteInvitationsListRequestObject.INVITATION_ID_LIST: [
                NOT_EXISTING_INVITATION_ID
            ]
        }
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation",
            json=body,
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(404, rsp.status_code)

    def test_delete_invalid_invitation(self):
        INVALID_INVITATION_ID = "null"
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation/{INVALID_INVITATION_ID}",
            headers=self.get_headers_for_token(MANAGER_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(403, rsp.status_code)

    @patch.object(EmailInvitationAdapter, "send_user_invitation_email")
    def test_success_send_user_invitation_email_multi_lang_support(
        self, mocked_send_email
    ):
        def get_language(mock):
            args = mock.call_args.args
            return args[2]

        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
            SendInvitationsRequestObject.LANGUAGE: Language.AR,
        }

        self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(CONTRIBUTOR_1_ID_DEPLOYMENT_X),
        )
        self.assertEqual(get_language(mocked_send_email), Language.AR)

        self.resend_invitation(TEST_EMAIL, mocked_send_email, language=Language.AR)
        self.assertEqual(get_language(mocked_send_email), Language.AR)

    def test_invite_patient_as_access_controller(self):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )
        self.assertEqual(200, rsp.status_code)

    def test_invite_patient_by_clinician(self):
        invitation_body = {
            SendInvitationsRequestObject.DEPLOYMENT_IDS: [DEPLOYMENT_ID],
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.USER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(CLINICIAN_ID),
        )
        self.assertEqual(200, rsp.status_code)

    def test_invite_access_controller_as_account_manager(self):
        org_id = "6156ad33a7082b29f6c6d0e8"
        invitation_body = {
            SendInvitationsRequestObject.CLIENT_ID: "c3",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: RoleName.ACCESS_CONTROLLER,
            SendInvitationsRequestObject.EMAILS: [TEST_EMAIL],
            SendInvitationsRequestObject.ORGANIZATION_ID: org_id,
        }
        headers = {
            **self.get_headers_for_token(ACCOUNT_MANAGER_ID),
            AuthorizationMiddleware.ORGANIZATION_HEADER_KEY: org_id,
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=headers,
        )
        self.assertEqual(200, rsp.status_code)


class ProxyInvitationTestCase(AbstractInvitationTestCase):
    @patch.object(EmailInvitationAdapter, "send_proxy_invitation_email")
    def test_success_proxy_invitation_sent_and_sign_up(self, mocked_send_email):
        rsp = self.send_proxy_invite(
            PATIENT_ID, submitter=CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(rsp.status_code, 200, rsp.json)
        self.assertTrue(rsp.json["ok"])

        invitation = self.get_invitation(invitation_email=TEST_EMAIL)
        user_data = get_invitation_sign_up_data(
            email=TEST_EMAIL, name="user1", invitation_code=invitation["code"]
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})
        roles = db_user[User.ROLES]
        self.assertEqual(RoleName.PROXY, roles[0][RoleAssignment.ROLE_ID])
        self.assertEqual(f"user/{PATIENT_ID}", roles[0][RoleAssignment.RESOURCE])
        args = mocked_send_email.call_args.args
        language = args[1]
        role_name = args[4]
        email = args[0]
        self.assertEqual(email, TEST_EMAIL)
        self.assertEqual(language, Language.EN)
        self.assertEqual(role_name, "contributor contributor")

    @patch.object(EmailInvitationAdapter, "send_proxy_invitation_email")
    def test_success_proxy_invitation_correct_deeplink_sent_from_cp(
        self, mocked_send_email
    ):
        cp_client_id = "c3"
        rsp = self.send_proxy_invite(
            PATIENT_ID, submitter=CONTRIBUTOR_1_ID_DEPLOYMENT_X, client_id=cp_client_id
        )
        self.assertEqual(rsp.status_code, 200)
        args = mocked_send_email.call_args.args
        client = args[2]
        self.assertNotEqual(client.clientId, cp_client_id)

    @patch.object(EmailInvitationAdapter, "send_proxy_invitation_email")
    def test_success_proxy_invitation_sent_with_patient_name(self, mocked_send_email):
        rsp = self.send_proxy_invite(PATIENT_ID)
        self.assertEqual(rsp.status_code, 200, rsp.json)
        self.assertTrue(rsp.json["ok"])

        kwargs = mocked_send_email.call_args.kwargs
        self.assertIn("dependant", kwargs)
        self.assertEqual(PATIENT_NAME, kwargs["dependant"])

    @patch.object(EmailInvitationAdapter, "send_proxy_invitation_email")
    def test_failure_proxy_invitation_resend_invitation_only_num_of_times_from_config(
        self, mocked_send_email
    ):
        rsp = self.send_proxy_invite(
            PATIENT_ID, submitter=CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(rsp.status_code, 200)
        for _ in range(5):
            rsp = self.resend_invitation(TEST_EMAIL, mocked_send_email)
            self.assertEqual(200, rsp.status_code)

        rsp = self.resend_invitation(TEST_EMAIL, mocked_send_email)
        self.assertEqual(400, rsp.status_code)

    def test_success_proxy_check_invitation_status(self):
        def get_proxy_invite_status(user_id):
            rsp = self.flask_client.get(
                f"/api/extensions/v1beta/user/{user_id}/proxy-invitations",
                headers=self.get_headers_for_token(user_id),
            )
            self.assertEqual(rsp.status_code, 200)
            return rsp

        rsp = self.send_proxy_invite(
            PATIENT_ID, submitter=CONTRIBUTOR_1_ID_DEPLOYMENT_X
        )
        self.assertEqual(rsp.status_code, 200)

        proxy_status = RetrieveProxyInvitationsResponseObject.Response.ProxyStatus
        # user didn't register yet
        rsp = get_proxy_invite_status(PATIENT_ID)
        self.assertEqual(rsp.json["status"], proxy_status.PENDING_SIGNUP.value)

        # user registered but didn't complete the on-boarding process
        invitation = self.get_invitation(invitation_email=TEST_EMAIL)
        user_data = get_invitation_sign_up_data(
            email=TEST_EMAIL, name="user1", invitation_code=invitation["code"]
        )
        self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        rsp = get_proxy_invite_status(PATIENT_ID)
        self.assertEqual(rsp.json["status"], proxy_status.PENDING_ONBOARDING.value)

        # user is fully onboarded
        self.mongo_database["user"].update_one(
            {User.EMAIL: TEST_EMAIL}, {"$set": {User.FINISHED_ONBOARDING: True}}
        )
        rsp = get_proxy_invite_status(PATIENT_ID)
        self.assertEqual(rsp.json["status"], proxy_status.ACTIVE.value)

    def test_failure_can_only_have_one_proxy_invitation_at_a_time(self):
        rsp = self.send_proxy_invite(PATIENT_ID)
        self.assertEqual(rsp.status_code, 200)

        rsp = self.send_proxy_invite(PATIENT_ID)
        self.assertEqual(rsp.status_code, 400)

    def test_success_delete_invitation(self):
        rsp = self.send_proxy_invite(PATIENT_ID)
        self.assertEqual(rsp.status_code, 200)
        invitation_id = rsp.json["ids"][0]
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation/{invitation_id}",
            headers=self.get_headers_for_token(PATIENT_ID),
        )
        self.assertEqual(rsp.status_code, 204)
        self.assertIsNone(self.get_invitation(invitation_id))

    def test_failure_delete_invitation_permission_with_other_user(self):
        rsp = self.send_proxy_invite(PATIENT_ID)
        self.assertEqual(rsp.status_code, 200)
        invitation_id = rsp.json["ids"][0]
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation/{invitation_id}",
            headers=self.get_headers_for_token(USER_2_ID_DEPLOYMENT_X),
        )
        self.assertEqual(rsp.status_code, 403)

    def test_success_can_delete_proxy_invite_made_by_contributor_on_behalf_of_patient(
        self,
    ):
        rsp = self.send_proxy_invite(PATIENT_ID, CONTRIBUTOR_1_ID_DEPLOYMENT_X)
        self.assertEqual(rsp.status_code, 200)
        invitation_id = rsp.json["ids"][0]

        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation/{invitation_id}",
            headers=self.get_headers_for_token(PATIENT_ID),
        )
        self.assertEqual(rsp.status_code, 204)

    def test_success_can_delete_proxy_invitation_as_contributor(self):
        contributor_same_level_as_patient = "5ff744265208ef492e895f1c"

        rsp = self.send_proxy_invite(PATIENT_ID)
        self.assertEqual(rsp.status_code, 200)
        invitation_id = rsp.json["ids"][0]
        rsp = self.flask_client.delete(
            f"/api/extensions/v1beta/deployment/invitation/{invitation_id}",
            headers=self.get_headers_for_token(contributor_same_level_as_patient),
        )
        self.assertEqual(rsp.status_code, 204)

    @patch.object(EmailInvitationAdapter, "send_proxy_invitation_email")
    def test_success_send_proxy_invitation_email_multi_lang_support(
        self, mocked_send_email
    ):
        def get_language(mock):
            args = mock.call_args.args
            return args[1]

        rsp = self.send_proxy_invite(PATIENT_ID, language=Language.AR)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(get_language(mocked_send_email), Language.AR)
        self.resend_invitation(TEST_EMAIL, mocked_send_email, language=Language.AR)
        self.assertEqual(get_language(mocked_send_email), Language.AR)

    def send_proxy_invite(
        self,
        user_id,
        submitter=None,
        email=TEST_EMAIL,
        role_id=RoleName.PROXY,
        client_id="ctest1",
        language=Language.EN,
    ):
        if not submitter:
            submitter = user_id

        invitation_body = {
            SendInvitationsRequestObject.PATIENT_ID: user_id,
            SendInvitationsRequestObject.CLIENT_ID: client_id,
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: role_id,
            SendInvitationsRequestObject.EMAILS: [email],
            SendInvitationsRequestObject.LANGUAGE: language,
        }

        return self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(submitter),
        )

    def test_success_call_center_role_can_send_proxy_invitation_on_behalf_of_user(self):
        valid_call_center_id = "602fa576c06fe59e3556142a"

        rsp = self.send_proxy_invite(PATIENT_ID, submitter=valid_call_center_id)
        self.assertEqual(rsp.status_code, 200)

    def test_invitation_with_custom_organization_role(self):
        test_email = "test@huma.com"
        org_custom_role_id = "6151051575fee50d15298adb"
        invitation_body = {
            SendInvitationsRequestObject.ORGANIZATION_ID: ORGANIZATION_ID,
            SendInvitationsRequestObject.CLIENT_ID: "ctest1",
            SendInvitationsRequestObject.PROJECT_ID: "ptest1",
            SendInvitationsRequestObject.ROLE_ID: org_custom_role_id,
            SendInvitationsRequestObject.EMAILS: [test_email],
        }
        rsp = self.flask_client.post(
            "/api/extensions/v1beta/deployment/send-invitation",
            json=invitation_body,
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID),
        )
        self.assertEqual(rsp.status_code, 200)
        self.assertTrue(rsp.json["ok"])

        invitation = self.mongo_database["invitation"].find_one(
            {Invitation.EMAIL: test_email}
        )
        user_data = get_invitation_sign_up_data(
            email=test_email, name="user1", invitation_code=invitation["code"]
        )
        rsp = self.flask_client.post(f"{self.auth_route}/signup", json=user_data)
        user_id = rsp.json["uid"]
        self.assertIsNotNone(user_id)
        db_user = self.mongo_database["user"].find_one({"_id": ObjectId(user_id)})
        role = db_user[User.ROLES][-1]
        self.assertEqual(org_custom_role_id, role[RoleAssignment.ROLE_ID])
        self.assertEqual(
            f"organization/{ORGANIZATION_ID}", role[RoleAssignment.RESOURCE]
        )

    def test_success_send_proxy_invitation_by_clinician(self):
        rsp = self.send_proxy_invite(PATIENT_ID, CLINICIAN_ID)
        self.assertEqual(rsp.status_code, 200, rsp.json)
        self.assertTrue(rsp.json["ok"])


class PublicInvitationRouteTestCase(AbstractInvitationTestCase):
    def test_validate_invitation_does_not_exist(self):
        rsp = self.flask_client.get(
            f"/api/public/v1beta/invitation-validity/not_existing_code",
        )
        self.assertEqual(404, rsp.status_code)

    def test_success_validate_invitation_with_code(self):
        rsp = self.flask_client.get(
            f"/api/public/v1beta/invitation-validity/{VALID_INVITATION_CODE}",
        )
        self.assertEqual(200, rsp.status_code)
