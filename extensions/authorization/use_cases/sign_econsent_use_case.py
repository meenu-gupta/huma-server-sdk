import logging
from functools import cached_property
from typing import Optional

from extensions.authorization.models.user import BoardingStatus
from extensions.authorization.router.user_profile_request import (
    SystemOffBoardUserRequestObject,
)
from extensions.authorization.use_cases.off_board_user_use_case import (
    OffBoardUserUseCase,
)
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.router.deployment_requests import SignEConsentRequestObject
from extensions.exceptions import EConsentInvalidAdditionalConsentAnswersException
from extensions.deployment.exceptions import (
    EConsentSignedError,
    OffBoardingRequiredError,
    DeploymentErrorCodes,
)
from extensions.deployment.tasks import update_econsent_pdf_location

from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.common.utils.json_utils import replace_values

logger = logging.getLogger(__file__)


class SignEConsentUseCase(UseCase):
    localization: dict
    request_object: SignEConsentRequestObject
    reject_option = EConsentLog.EConsentOption.NOT_PARTICIPATE
    off_board_reason = BoardingStatus.ReasonOffBoarded.USER_UNSIGNED_EICF

    @autoparams()
    def __init__(self, ec_repo: EConsentRepository, dep_repo: DeploymentRepository):
        self._econsent_repo = ec_repo
        self._deployment_repo = dep_repo

    def execute(self, request_object):
        self.request_object = request_object
        self.localization = self.request_object.user.localization
        return super(SignEConsentUseCase, self).execute(request_object)

    def process_request(self, request_object: SignEConsentRequestObject):
        if self._is_econsent_already_signed():
            raise EConsentSignedError("This EConsent was already signed by this user.")

        if self._is_consent_rejected():
            return self._off_board_user()

        inserted_econsent_log_id = self._create_econsent_log_and_update_pdf()
        return Response(value=inserted_econsent_log_id)

    @cached_property
    def _latest_consent(self) -> Optional[EConsent]:
        return self.request_object.user.deployment.latest_econsent

    def _is_econsent_already_signed(self) -> bool:
        if not self._latest_consent:
            return True

        log_count = self._econsent_repo.retrieve_log_count(
            consent_id=self._latest_consent.id,
            revision=self._latest_consent.revision,
            user_id=self.request_object.userId,
        )
        return log_count > 0

    def _is_consent_rejected(self) -> bool:
        return self.request_object.consentOption == self.reject_option

    def _off_board_user(self) -> None:
        OffBoardUserUseCase().execute(
            SystemOffBoardUserRequestObject.from_dict(
                {
                    SystemOffBoardUserRequestObject.USER_ID: self.request_object.userId,
                    SystemOffBoardUserRequestObject.REASON: self.off_board_reason,
                }
            )
        )
        raise OffBoardingRequiredError(
            DeploymentErrorCodes.OFF_BOARDING_USER_UNSIGNED_EICF
        )

    def _create_econsent_log_and_update_pdf(self) -> str:
        log = self.request_object
        del self.request_object.user
        inserted_log_id = self._econsent_repo.create_econsent_log(
            deployment_id=log.deploymentId, econsent_log=log
        )
        self._update_pdf_location(inserted_log_id)
        return inserted_log_id

    def _update_pdf_location(self, log_id: str) -> None:
        log = self.request_object
        econsent_dict = self._latest_consent.to_dict(ignored_fields=[EConsent.ID])
        econsent_log_dict = log.to_dict(
            ignored_fields=(EConsentLog.USER_ID, EConsentLog.ECONSENT_ID)
        )

        answers = self._get_additional_answers(
            log.additionalConsentAnswers,
            self._latest_consent.additionalConsentQuestions,
        )

        econsent_dict = replace_values(econsent_dict, self.localization)
        econsent_log_dict = replace_values(econsent_log_dict, self.localization)
        additional_answers = [replace_values(x, self.localization) for x in answers]
        other_strings = replace_values(
            {
                "participant_name": "hu_econsent_participant_name",
                "date_signature": "hu_econsent_date_signature",
                "signature": "hu_econsent_signature",
                "no": "hu_econsent_no",
                "yes": "hu_econsent_yes",
            },
            self.localization,
        )

        update_econsent_pdf_location.delay(
            econsent=econsent_dict,
            econsent_log=econsent_log_dict,
            deployment_id=log.deploymentId,
            full_name=log.get_full_name(),
            econsent_log_id=log_id,
            request_id=log.requestId,
            answers=additional_answers,
            other_strings=other_strings,
        )

    @staticmethod
    def _get_additional_answers(answers, questions) -> list:
        if not (answers and questions):
            return []

        additional_answers = []
        additional_questions = sorted(questions, key=lambda i: i.order)
        for question in additional_questions:
            if not answers.get(question.type) is None:
                question_data = {
                    "question": question.text,
                    "format": question.format.value,
                    "answer": answers.get(question.type),
                }
                additional_answers.append(question_data)
                answers.pop(question.type, None)
        if answers:
            raise EConsentInvalidAdditionalConsentAnswersException(
                ", ".join(answers.keys())
            )
        return additional_answers
