from unittest import TestCase
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.deployment.models.deployment import Deployment, Features, SummaryReport
from extensions.export_deployment.router.report_routers import generate_report
from extensions.export_deployment.router.utils import (
    is_summary_reports_enabled_for_deployment,
)

app = Flask("test")
REPORT_ROUTERS = "extensions.export_deployment.router.report_routers"


class SummaryReportTestCase(TestCase):
    @patch(f"{REPORT_ROUTERS}.send_file")
    @patch(f"{REPORT_ROUTERS}.get_request_json_dict_or_raise_exception")
    @patch(f"{REPORT_ROUTERS}.GenerateSummaryReportRequestObject")
    @patch(f"{REPORT_ROUTERS}.GenerateSummaryReportUseCase")
    def test_generate_report(self, use_case, req_obj, body, response):
        body.return_value = {"format": "PDF"}
        user_id = "randomUserId"
        deployment = Deployment(
            features=Features(summaryReport=SummaryReport(enabled=True))
        )

        with app.app_context() as context:
            context.g.user = MagicMock()
            context.g.path_user = MagicMock()
            context.g.authz_path_user = MagicMock(deployment=deployment)
            generate = generate_report.__wrapped__.__wrapped__  # remove decorators
            generate(user_id)
        req_obj.from_dict.assert_called_once()
        use_case.assert_called_once()
        use_case().execute.assert_called_once()
        response.assert_called_once()

    @patch(f"{REPORT_ROUTERS}.send_file")
    @patch(f"{REPORT_ROUTERS}.get_request_json_dict_or_raise_exception")
    @patch(f"{REPORT_ROUTERS}.GenerateSummaryReportRequestObject")
    @patch(f"{REPORT_ROUTERS}.GenerateSummaryReportUseCase")
    def test_generate_report_feature_disabled(self, use_case, req_obj, body, response):
        body.return_value = {"format": "PDF"}
        user_id = "randomUserId"
        deployment = Deployment(
            features=Features(summaryReport=SummaryReport(enabled=False))
        )

        with app.app_context() as context:
            context.g.user = MagicMock()
            context.g.path_user = MagicMock()
            context.g.authz_path_user = MagicMock(deployment=deployment)
            generate = generate_report.__wrapped__.__wrapped__  # remove decorators
            result = generate(user_id)

        self.assertEqual(("<h1>Feature is not enabled</h1>", 404), result)
        req_obj.from_dict.assert_not_called()
        use_case.assert_not_called()
        use_case().execute.assert_not_called()
        response.assert_not_called()

    def test_false_is_summary_reports_enabled_for_deployment__no_deployment(self):
        res = is_summary_reports_enabled_for_deployment(None)
        self.assertFalse(res)

    def test_false_is_summary_reports_enabled_for_deployment__no_features(self):
        deployment = Deployment()
        res = is_summary_reports_enabled_for_deployment(deployment)
        self.assertFalse(res)

    def test_false_is_summary_reports_enabled_for_deployment__no_summary_report(self):
        deployment = Deployment(features=Features())
        res = is_summary_reports_enabled_for_deployment(deployment)
        self.assertFalse(res)

    def test_false_is_summary_reports_enabled_for_deployment__summary_report_disabled(
        self,
    ):
        deployment = Deployment(
            features=Features(summaryReport=SummaryReport(enabled=False))
        )
        res = is_summary_reports_enabled_for_deployment(deployment)
        self.assertFalse(res)

    def test_true_is_summary_reports_enabled_for_deployment__no_deployment(self):
        deployment = Deployment(
            features=Features(summaryReport=SummaryReport(enabled=True))
        )
        res = is_summary_reports_enabled_for_deployment(deployment)
        self.assertTrue(res)
