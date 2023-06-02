import unittest
from unittest.mock import MagicMock, patch

from extensions.module_result.questionnaires.pam_questionnaire_calculator import (
    get_pam_config,
    PAMQuestionnaireCalculator,
)

PATH = "extensions.module_result.questionnaires.pam_questionnaire_calculator"


class MockServerConfig:
    instance = MagicMock()
    moduleResult = MagicMock()


class PAMQuestionnaireCalculatorTestCase(unittest.TestCase):
    def test_get_pam_config(self):
        config = MockServerConfig()
        res = get_pam_config(MagicMock(), config)
        self.assertEqual(res, config.moduleResult.pamIntegration)

    @patch(f"{PATH}.inject")
    @patch("extensions.deployment.service.deployment_service.DeploymentService")
    def test_calculate(self, deployment_service, inject):
        primitive = MagicMock()
        pam_client = MagicMock()
        pam_client.submit_survey.return_value = 1, 1
        inject.instance.return_value = pam_client
        calc = PAMQuestionnaireCalculator()
        calc.calculate(primitive, MagicMock())

        deployment_service().retrieve_deployment.assert_called_with(
            primitive.deploymentId
        )
        pam_client.submit_survey.assert_called_with(
            primitive=primitive,
            third_party_identifier=inject.instance()
            .retrieve_user_profile()
            .pamThirdPartyIdentifier,
        )


if __name__ == "__main__":
    unittest.main()
