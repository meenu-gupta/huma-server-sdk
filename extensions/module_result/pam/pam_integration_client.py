import logging
import random
import string
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Union

import requests

from extensions.exceptions import HttpErrorOnPamQuestionnaire
from extensions.module_result.config.integration_client import IntegrationClient
from extensions.module_result.config.pam_integration_client_config import (
    PAMIntegrationClientConfig,
)
from extensions.module_result.models.primitives import Primitive, Questionnaire

log = logging.getLogger(__name__)


class PAMIntegrationClient(IntegrationClient):
    class PAMAnswer(Enum):
        DISAGREE_STRONGLY = "Disagree Strongly"
        DISAGREE = "Disagree"
        AGREE = "Agree"
        AGREE_STRONGLY = "Agree Strongly"
        NA = "N/A"

    def __init__(self, config: PAMIntegrationClientConfig):
        self._config = config
        self._submit_survey_uri = self._config.submitSurveyURI
        self._enroll_user_uri = self._config.enrollUserURI
        self._client_ext_id = self._config.clientExtID
        self._client_pass_key = self._config.clientPassKey
        self._sub_group_id = self._config.subgroupExtID
        self._timeout = self._config.timeout
        self._headers = {"Accept": "application/xml", "Content-Type": "text/xml"}

    def call_api_endpoint(self, primitive: Primitive) -> Union[Primitive, None]:
        return

    def enroll_user(self, email: str) -> str:
        third_party_identifier = self.generate_identifier()
        enroll_user_body = self._create_enroll_user_request_body(
            identifier=third_party_identifier, email=email
        )
        return self._enroll_user(enroll_user_body)

    def submit_survey(
        self, primitive: Primitive, third_party_identifier: str
    ) -> tuple[float, float]:
        if not isinstance(primitive, Questionnaire):
            raise Exception(
                f"Ignoring primitive of type {type(primitive).__name__} "
                f"(expected {Questionnaire.__name__})"
            )

        answers = self._retrieve_pam_questionnaire_answers(primitive)
        body = self._create_submit_survey_request_body(third_party_identifier, answers)

        return self._submit_survey_result(body)

    @staticmethod
    def generate_identifier():
        alpha_numeric = string.ascii_letters + string.digits
        return "".join(random.choice(alpha_numeric) for _ in range(25))

    @staticmethod
    def _retrieve_pam_questionnaire_answers(
        questionnaire_result: Questionnaire,
    ) -> list[int]:
        answers = [answer.answerText for answer in questionnaire_result.answers]
        answers_numeric = []
        for answer in answers:
            if answer == PAMIntegrationClient.PAMAnswer.DISAGREE_STRONGLY.value:
                answers_numeric.append(1)
            elif answer == PAMIntegrationClient.PAMAnswer.DISAGREE.value:
                answers_numeric.append(2)
            elif answer == PAMIntegrationClient.PAMAnswer.AGREE.value:
                answers_numeric.append(3)
            elif answer == PAMIntegrationClient.PAMAnswer.AGREE_STRONGLY.value:
                answers_numeric.append(4)
            elif answer == PAMIntegrationClient.PAMAnswer.NA.value:
                answers_numeric.append(0)
            else:
                raise Exception(f"Unknown PAM questionnaire answer: {answer} ")
        return answers_numeric

    def _submit_survey_result(self, body: str):
        response = requests.post(
            url=self._submit_survey_uri,
            data=body,
            headers=self._headers,
            timeout=self._timeout,
        )
        score = 0
        level = 0

        log.info(
            "Received PAM response status: %d, content: %s",
            response.status_code,
            response.content,
        )
        response.raise_for_status()

        pam_xml_res = ET.fromstring(response.content)
        status_code = pam_xml_res.find("StatusCode").text
        if status_code == "Success_SurveySubmit":
            response_data = pam_xml_res.find("SurveyResult").find("ResponseData")
            if response_data[0].get("id") == "PAMLevel":
                level = float(response_data[0].get("value"))
            if response_data[1].get("id") == "PAMScore":
                score = float(response_data[1].get("value"))
        else:
            error = status_code
            log.error("Error %s when submitting survey result", error)
            raise HttpErrorOnPamQuestionnaire

        return score, level

    def _enroll_user(self, body: str):
        response = requests.post(
            url=self._enroll_user_uri,
            data=body,
            headers=self._headers,
            timeout=self._timeout,
        )

        response.raise_for_status()

        third_party_identifier = None

        pam_xml_res = ET.fromstring(response.content)
        status_code = pam_xml_res.find("StatusCode").text
        if status_code == "Success_Register":
            third_party_identifier = pam_xml_res.find("ThirdPartyIdentifier").text
        else:
            error = status_code
            log.error("Error %s when submitting survey result", error)

        return third_party_identifier

    def _create_submit_survey_request_body(self, identifier: str, answers: list[int]):
        if len(answers) != 13:
            raise Exception(
                "PAM 13 questionnaire should have 13 answers, but got %d", len(answers)
            )

        return """
        <request>
            <user>
                <ClientExtID>%s</ClientExtID>
                <ClientPassKey>%s</ClientPassKey>
                <thirdpartyidentifier>%s</thirdpartyidentifier>
            </user>
            <Survey>
                <Language>enu</Language>
                <SurveyName>PAM13_S</SurveyName>
                <Administration day="1" month="1" year="2019"/>
                <SurveyResponse Age="" Gender="" SurveyDeliveryMode="System Name">
                    <Answer ID="PA1">%s</Answer>
                    <Answer ID="PA2">%s</Answer>
                    <Answer ID="PA3">%s</Answer>
                    <Answer ID="PA4">%s</Answer>
                    <Answer ID="PA5">%s</Answer>
                    <Answer ID="PA6">%s</Answer>
                    <Answer ID="PA7">%s</Answer>
                    <Answer ID="PA8">%s</Answer>
                    <Answer ID="PA9">%s</Answer>
                    <Answer ID="PA10">%s</Answer>
                    <Answer ID="PA11">%s</Answer>
                    <Answer ID="PA12">%s</Answer>
                    <Answer ID="PA13">%s</Answer>
                </SurveyResponse>
            </Survey>
        </request>""" % (
            self._client_ext_id,
            self._client_pass_key,
            identifier,
            *answers,
        )

    def _create_enroll_user_request_body(self, identifier: str, email: str):
        return """
        <request>
            <user>
                <ClientExtID>%s</ClientExtID>
                <ClientPassKey>%s</ClientPassKey>
                <SubgroupExtID>%s</SubgroupExtID>
                <thirdpartyidentifier>%s</thirdpartyidentifier>
                <primaryemail>%s</primaryemail>
            </user>
        </request>""" % (
            self._client_ext_id,
            self._client_pass_key,
            self._sub_group_id,
            identifier,
            email,
        )
