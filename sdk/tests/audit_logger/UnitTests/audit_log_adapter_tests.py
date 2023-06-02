import unittest
from unittest.mock import MagicMock, patch

from sdk.audit_logger.adapter.audit_log_adapter import AuditLogAdapter

ADAPTER_PATH = "sdk.audit_logger.adapter.audit_log_adapter"


class AuditLogAdapterTestCase(unittest.TestCase):
    @patch(f"{ADAPTER_PATH}.inject")
    def test_success_log_error(self, inject):
        audit_adapter = MagicMock()
        msg = "some_message"
        adapter = AuditLogAdapter(audit_adapter)
        methods_to_test = {
            adapter.error: "ERROR",
            adapter.info: "INFO",
            adapter.debug: "DEBUG",
        }
        for method, err_level in methods_to_test.items():
            method(msg)
            inject.instance().create_log.assert_called_with(
                {"label": None, "level": err_level, "message": msg}
            )


if __name__ == "__main__":
    unittest.main()
