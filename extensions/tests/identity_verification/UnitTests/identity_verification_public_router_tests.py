import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.identity_verification.router.identity_verification_public_router import (
    receive_onfido_result,
)

IDENTITY_PUBLIC_ROUTER_PATH = (
    "extensions.identity_verification.router.identity_verification_public_router"
)

testapp = Flask(__name__)
testapp.app_context().push()


class IdentityVerificationPublicRouterTestCase(unittest.TestCase):
    @patch(f"{IDENTITY_PUBLIC_ROUTER_PATH}.check_onfido_signature", MagicMock())
    @patch(f"{IDENTITY_PUBLIC_ROUTER_PATH}.OnfidoCallBackVerificationRequestObject")
    @patch(f"{IDENTITY_PUBLIC_ROUTER_PATH}.ReceiveOnfidoResultUseCase")
    def test_success_receive_onfido_result(self, use_case, req_obj):
        payload = {}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            receive_onfido_result()
            req_obj.from_dict.assert_called_with(payload)
            use_case().execute.assert_called_with(req_obj.from_dict())


if __name__ == "__main__":
    unittest.main()
