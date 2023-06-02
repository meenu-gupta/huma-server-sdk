import unittest
from unittest.mock import MagicMock, patch

from extensions.module_result.models.primitives import Questionnaire
from extensions.module_result.pam.pam_integration_client import PAMIntegrationClient

PATH = "extensions.module_result.pam.pam_integration_client"


class PAMIntegrationClientTestCase(unittest.TestCase):
    @patch(f"{PATH}.PAMIntegrationClient.generate_identifier")
    @patch(f"{PATH}.PAMIntegrationClient._create_enroll_user_request_body")
    @patch(f"{PATH}.PAMIntegrationClient._enroll_user")
    def test_enroll_user(
        self, enroll, create_enroll_user_request_body, generate_identifier
    ):
        email = "some_email@huma.com"
        client = PAMIntegrationClient(MagicMock())
        client.enroll_user(email)
        create_enroll_user_request_body.assert_called_with(
            identifier=generate_identifier(), email=email
        )
        generate_identifier.assert_called()
        enroll.assert_called_with(create_enroll_user_request_body())

    @patch(f"{PATH}.PAMIntegrationClient._retrieve_pam_questionnaire_answers")
    @patch(f"{PATH}.PAMIntegrationClient._create_submit_survey_request_body")
    @patch(f"{PATH}.PAMIntegrationClient._submit_survey_result")
    def test_submit_survey(self, submit_survey, create_submit_survey, retrieve_pam):
        primitive = MagicMock(spec_set=Questionnaire)
        third_party_identifier = "a"
        client = PAMIntegrationClient(MagicMock())
        client.submit_survey(primitive, third_party_identifier)
        submit_survey.assert_called_with(create_submit_survey())
        create_submit_survey.assert_called_with()
        retrieve_pam.assert_called_with(primitive)

    def test_generate_identifier(self):
        res = PAMIntegrationClient.generate_identifier()
        self.assertEqual(25, len(res))

    def test_retrieve_pam_questionnaire_answers(self):
        questionnaire_result = MagicMock()
        answer = MagicMock()
        answer.answerText = PAMIntegrationClient.PAMAnswer.DISAGREE_STRONGLY.value
        questionnaire_result.answers = [answer]
        client = PAMIntegrationClient(MagicMock())
        res = client._retrieve_pam_questionnaire_answers(questionnaire_result)
        self.assertEqual([1], res)

    @patch(f"{PATH}.requests")
    def test_submit_survey_result_external_request(self, requests):
        body = "a"
        response = MagicMock()
        response.content = '<UserSurveyResponseData xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><StatusCode>Success_SurveySubmit</StatusCode><StatusMessage>Submit User Survey success.</StatusMessage><SurveyEnteredDateTime>2019-01-01T00:00:00</SurveyEnteredDateTime><SurveyName>PAM13_S</SurveyName><SurveyResult><ResponseData><Type id="PAMLevel" value="1"/><Type id="PAMScore" value="34.20"/></ResponseData></SurveyResult><ThirdPartyIdentifier>HumaUser42</ThirdPartyIdentifier></UserSurveyResponseData>'

        config = MagicMock()
        client = PAMIntegrationClient(config)
        requests.post.return_value = response
        client._submit_survey_result(body)
        requests.post.assert_called_with(
            url=config.submitSurveyURI,
            data=body,
            headers={"Accept": "application/xml", "Content-Type": "text/xml"},
            timeout=config.timeout,
        )

    @patch(f"{PATH}.requests")
    def test_enroll_user_external_request(self, requests):
        body = "a"
        response = MagicMock()
        response.content = '<RegisterResponseData xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><StatusCode>Success_Register</StatusCode><StatusMessage>User successfully registered.</StatusMessage><ExternalUserID>200727-E0JH2GV1</ExternalUserID><NationalPatientIdentifier i:nil="true"/><ThirdPartyIdentifier>27VInKyucB9A7aVvrPE9c4d24pli6grg</ThirdPartyIdentifier></RegisterResponseData>'

        config = MagicMock()
        client = PAMIntegrationClient(config)
        requests.post.return_value = response
        client._enroll_user(body)
        requests.post.assert_called_with(
            url=config.enrollUserURI,
            data=body,
            headers={"Accept": "application/xml", "Content-Type": "text/xml"},
            timeout=config.timeout,
        )


if __name__ == "__main__":
    unittest.main()
