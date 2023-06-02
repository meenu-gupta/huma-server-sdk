import json
import unittest
from unittest.mock import patch, MagicMock

from onfido.exceptions import OnfidoInvalidSignatureError

from extensions.config.config import ExtensionServer
from extensions.identity_verification.router.policies import check_onfido_signature
from sdk.common.adapter.identity_verification_adapter import IdentityVerificationAdapter
from sdk.common.adapter.onfido.onfido_adapter import OnfidoAdapter
from sdk.common.adapter.onfido.onfido_config import OnfidoConfig
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig, Adapters

SAMPLE_PAYLOAD_DATA = {
    "payload": {
        "resource_type": "check",
        "action": "check.completed",
        "object": {
            "id": "26411331-15e2-4a11-9ba0-b135d4131902",
            "status": "complete",
            "completed_at_iso8601": "2021-02-24T20:57:58Z",
            "href": "https://api.onfido.com/v3/checks/26411331-15e2-4a11-9ba0-b135d4131902",
        },
    }
}


class MockFlaskRequest:
    instance = MagicMock()
    data = json.dumps(SAMPLE_PAYLOAD_DATA).encode("utf-8")
    headers = {
        "X-SHA2-Signature": "593781f6193cdddb33437aa0877f07356e1e5d83badb134b15fdc64c69247fd0"
    }


class OnfidoHeadersTestCase(unittest.TestCase):
    def setUp(self) -> None:
        adapters = Adapters(onfido=OnfidoConfig(webhookToken="secret_webhook_token"))
        self.config = PhoenixServerConfig(server=ExtensionServer(adapters=adapters))

        def bind(binder):
            binder.bind(PhoenixServerConfig, self.config)
            binder.bind_to_provider(
                IdentityVerificationAdapter, lambda: OnfidoAdapter(self.config)
            )

        inject.clear_and_configure(bind)

    @patch("extensions.identity_verification.router.policies.request", MockFlaskRequest)
    def test_success_verify_header(self):
        try:
            check_onfido_signature()
        except OnfidoInvalidSignatureError:
            self.fail()

    @patch("extensions.identity_verification.router.policies.request", MockFlaskRequest)
    def test_failure_verify_not_acceptable_header(self):
        self.config.server.adapters.onfido.webhookToken = "wrong_token"
        with self.assertRaises(OnfidoInvalidSignatureError):
            check_onfido_signature()


if __name__ == "__main__":
    unittest.main()
