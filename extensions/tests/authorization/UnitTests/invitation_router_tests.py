import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.authorization.router.invitation_response_objects import (
    DeleteInvitationsListResponse,
    ResendInvitationsListResponse,
)
from extensions.authorization.router.invitation_router import (
    send_user_invitation,
    resend_user_invitation_list,
    delete_invitation_list,
)
from extensions.authorization.router.public_invitation_router import (
    invitation_validity_check,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.audit_logger import AuditLog

INVITATION_ROUTER_PATH = "extensions.authorization.router.invitation_router"
PUBLIC_INVITATION_ROUTER_PATH = (
    "extensions.authorization.router.public_invitation_router"
)
INVITATION_OBJECT_ID = "615f60b3d61eee4a2623cf95"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{INVITATION_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class InvitationRouterTestCase(unittest.TestCase):
    @patch(f"{INVITATION_ROUTER_PATH}.g")
    @patch(f"{INVITATION_ROUTER_PATH}.jsonify")
    @patch(f"{INVITATION_ROUTER_PATH}.SendInvitationsRequestObject")
    @patch(f"{INVITATION_ROUTER_PATH}.SendInvitationsUseCase")
    def test_success_send_user_invitation(self, use_case, req_obj, jsonify, g):
        g.return_value = MagicMock()
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            send_user_invitation()
            payload[req_obj.SUBMITTER] = g.authz_user
            req_obj.from_dict.assert_called_with(payload)
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{PUBLIC_INVITATION_ROUTER_PATH}.jsonify")
    @patch(f"{PUBLIC_INVITATION_ROUTER_PATH}.InvitationValidityRequestObject")
    @patch(f"{PUBLIC_INVITATION_ROUTER_PATH}.InvitationValidityUseCase")
    def test_success_validate_invitation(self, use_case, req_obj, jsonify):
        invitation_code = "sample_invitation_code"
        with testapp.test_request_context("/", method="GET") as _:
            invitation_validity_check(invitation_code)
            req_obj.from_dict.assert_called_with(
                {req_obj.INVITATION_CODE: invitation_code}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{INVITATION_ROUTER_PATH}.ResendInvitationsListRequestObject")
    @patch(f"{INVITATION_ROUTER_PATH}.ResendInvitationsListUseCase")
    def test_resend_user_invitation_list(self, use_case, req_obj_mock):

        payload = {"a": "b"}
        use_case().execute.return_value = ResendInvitationsListResponse(
            resent_invitations=1
        )
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            rsp, status = resend_user_invitation_list()
            self.assertEqual(1, rsp.json["resentInvitations"])
            use_case().execute.assert_called_with(req_obj_mock.from_dict())

    @patch(f"{INVITATION_ROUTER_PATH}.DeleteInvitationsListRequestObject")
    @patch(f"{INVITATION_ROUTER_PATH}.DeleteInvitationsListUseCase")
    def test_delete_user_invitation_list(self, use_case, req_obj_mock):

        payload = {"a": "b"}
        use_case().execute.return_value = DeleteInvitationsListResponse(1)
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            rsp, status = delete_invitation_list()
            self.assertEqual(1, rsp.json["deletedInvitations"])
            use_case().execute.assert_called_with(req_obj_mock.from_dict())

    @patch(f"{INVITATION_ROUTER_PATH}.DeleteInvitationsListUseCase")
    def test_delete_user_invitation_list_with_wrong_type(self, use_case):

        payload = {
            "invitationIdList": [INVITATION_OBJECT_ID],
            "invitationType": "WRONG",
        }
        use_case().execute.return_value = DeleteInvitationsListResponse(1)
        with self.assertRaises(ConvertibleClassValidationError):
            with testapp.test_request_context("/", method="POST", json=payload) as _:
                delete_invitation_list()


if __name__ == "__main__":
    unittest.main()
