import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.identity_verification.router.identity_verification_router import (
    create_user_verification_log,
    generate_identity_verification_sdk_token,
)
from sdk.phoenix.audit_logger import AuditLog

IDENTITY_VERIFICATION_ROUTER_PATH = (
    "extensions.identity_verification.router.identity_verification_router"
)
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{IDENTITY_VERIFICATION_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class IdentityVerificationRouterTestCase(unittest.TestCase):
    @patch(f"{IDENTITY_VERIFICATION_ROUTER_PATH}.jsonify")
    @patch(f"{IDENTITY_VERIFICATION_ROUTER_PATH}.CreateVerificationLogUseCase")
    @patch(f"{IDENTITY_VERIFICATION_ROUTER_PATH}.CreateVerificationLogRequestObject")
    @patch(f"{IDENTITY_VERIFICATION_ROUTER_PATH}.g")
    def test_success_create_user_verification_log(
        self, g_mock, req_obj, use_case, jsonify
    ):
        payload = {"a": "b"}
        g_mock.user = MagicMock()
        g_mock.authz_user = MagicMock()
        g_mock.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_user_verification_log()
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.USER_ID: g_mock.user.id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{IDENTITY_VERIFICATION_ROUTER_PATH}.jsonify")
    @patch(
        f"{IDENTITY_VERIFICATION_ROUTER_PATH}.GenerateIdentityVerificationSdkTokenUseCase"
    )
    @patch(
        f"{IDENTITY_VERIFICATION_ROUTER_PATH}.GenerateIdentityVerificationTokenRequestObject"
    )
    @patch(f"{IDENTITY_VERIFICATION_ROUTER_PATH}.g")
    def test_success_generate_identity_verification_sdk_token(
        self, g_mock, req_obj, use_case, jsonify
    ):
        payload = {"a": "b"}
        g_mock.get = MagicMock()
        g_mock.get("user_agent").return_value = SAMPLE_ID
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            generate_identity_verification_sdk_token()
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.USER_ID: g_mock.user.id,
                    req_obj.APPLICATION_ID: g_mock.get().bundle_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())


if __name__ == "__main__":
    unittest.main()
