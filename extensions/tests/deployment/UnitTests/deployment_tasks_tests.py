import unittest
from unittest.mock import MagicMock, patch

from extensions.deployment.exceptions import EConsentPdfGenerationError
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.tasks import (
    calculate_stats_per_deployment,
    update_econsent_pdf_location,
)

SAMPLE_ID = "61f952420a1ef14e3b1ec7cb"
TASKS_PATH = "extensions.deployment.tasks"


class DeploymentTasksTestCase(unittest.TestCase):
    @patch(f"{TASKS_PATH}.DeploymentService")
    @patch(f"{TASKS_PATH}.DeploymentStatsCalculator", MagicMock())
    @patch(f"{TASKS_PATH}.UpdateDeploymentRequestObject")
    def test_calculate_stats_per_deployment(self, mock_req, mock_service):
        mock_service().retrieve_deployments = MagicMock(
            return_value=([Deployment(id=SAMPLE_ID)], 1)
        )
        calculate_stats_per_deployment()
        mock_req.from_dict.assert_called_once()
        mock_service().update_deployment.assert_called_once()

    @patch(f"{TASKS_PATH}.inject", MagicMock())
    @patch(f"{TASKS_PATH}.pdfkit", MagicMock())
    @patch(f"{TASKS_PATH}.BytesIO", MagicMock())
    @patch(f"{TASKS_PATH}.report_exception")
    def test_update_econsent_pdf_location(self, mock_report_exception):
        update_econsent_pdf_location(
            {EConsent.REVISION: 1, EConsent.SECTIONS: [], EConsent.TITLE: "title"},
            {
                EConsentLog.USER_ID: SAMPLE_ID,
                EConsentLog.SIGNATURE: {
                    "key": "key",
                    "region": "eu",
                    "bucket": "bucket",
                },
            },
            "deployment id",
            "full name",
            "econsent_log_id",
            "request_id",
            [{"a": "b"}],
            {},
        )

        with self.assertRaises(KeyError):
            update_econsent_pdf_location(
                {EConsent.REVISION: 1, EConsent.SECTIONS: [], EConsent.TITLE: "title"},
                {
                    EConsentLog.SIGNATURE: {
                        "key": "key",
                        "region": "eu",
                        "bucket": "bucket",
                    }
                },
                "deployment id",
                "full name",
                "econsent_log_id",
                "request_id",
                [{"a": "b"}],
                {},
            )

        with self.assertRaises(EConsentPdfGenerationError):
            update_econsent_pdf_location(
                {
                    EConsent.ID: SAMPLE_ID,
                    EConsent.REVISION: 1,
                    EConsent.SECTIONS: [],
                    EConsent.TITLE: "title",
                },
                {EConsentLog.USER_ID: SAMPLE_ID, EConsentLog.SIGNATURE: ""},
                "deployment id",
                "full name",
                "econsent_log_id",
                "request_id",
                [{"a": "b"}],
                {},
            )
            mock_report_exception.assert_called_once()
