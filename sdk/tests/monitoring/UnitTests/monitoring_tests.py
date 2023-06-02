import unittest
from unittest.mock import patch
from sdk.common.monitoring.monitoring import report_exception

MONITORING_PATH = "sdk.common.monitoring.monitoring"


class MonitoringTestCase(unittest.TestCase):
    @patch(f"{MONITORING_PATH}.inject")
    def test_report_exception(self, mock_inject):
        mock_inject.instance().is_configured.return_value = True

        error = "error"

        report_exception(error=error)

        mock_inject.instance.assert_called()
        mock_inject.instance().report_exception.assert_called()

    @patch(f"{MONITORING_PATH}.ErrorForm")
    @patch(f"{MONITORING_PATH}.inject")
    def test_report_exception_with_context(self, mock_inject, mock_error_form):
        mock_inject.instance().is_configured.return_value = True

        error = "error"
        context_name = "name"
        context_content = {"content": 1}

        report_exception(
            error=error, context_name=context_name, context_content=context_content
        )

        mock_inject.instance.assert_called()
        mock_inject.instance().report_exception.assert_called()
        mock_error_form.ContextForm.assert_called_with(
            name=context_name, content=context_content
        )


if __name__ == "__main__":
    unittest.main()
