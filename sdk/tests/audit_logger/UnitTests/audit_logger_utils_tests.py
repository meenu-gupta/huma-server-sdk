from unittest import TestCase

from sdk.common.utils.sensitive_data import redact_data, MASK


class AuditLoggerUtils(TestCase):
    def test_success_hide_sensitive_field(self):
        data = None
        result = None
        self.assertEqual(result, redact_data(data))

        data = "sample"
        result = "sample"
        self.assertEqual(result, redact_data(data))

        data = {"password": "sample"}
        result = {"password": MASK}
        self.assertEqual(result, redact_data(data))

        data = [{"token": "sample"}]
        result = [{"token": MASK}]
        self.assertEqual(result, redact_data(data))

        data = [{"sample": {"token": "sample"}}]
        result = [{"sample": {"token": MASK}}]
        self.assertEqual(result, redact_data(data))

        data = [{"sample": [{"token": "sample"}]}]
        result = [{"sample": [{"token": MASK}]}]
        self.assertEqual(result, redact_data(data))
