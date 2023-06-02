from typing import Optional

from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.primitives import (
    IKDC,
    Questionnaire,
    Primitive,
    QuestionnaireAnswer,
    Symptoms,
    SportsActivity,
    KneeFunction,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.modules.licensed_questionnaire_module import (
    LicensedQuestionnaireModule,
)
from extensions.module_result.questionnaires.ikdc_questionnaire_calculator import (
    IKDCQuestionnaireCalculator,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.validators import str_to_int


class IKDCModule(LicensedQuestionnaireModule):
    moduleId = "KneeHealthIKDC"
    primitives = [Questionnaire, IKDC]
    calculator = IKDCQuestionnaireCalculator
    ragEnabled = True
    minimumAnswered = 16

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        if len(primitives) > 1:
            raise InvalidRequestException("Only one questionnaire can be submitted")

        questionnaire = primitives[0]
        if not isinstance(questionnaire, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        scoring_answers = self.filter_scoring_answers(questionnaire.answers)
        self._validate_minimum_answers(scoring_answers)
        ikdc = self._build_ikdc_from_questionnaire(questionnaire)
        ikdc.scoring_answers = scoring_answers
        primitives.append(ikdc)
        return super().preprocess(primitives, user)

    def _build_ikdc_from_questionnaire(self, questionnaire: Questionnaire):
        self._add_score_to_answers(questionnaire.answers)
        ikdc_dict = {
            **questionnaire.to_dict(include_none=False),
            IKDC.SYMPTOMS: self._build_nested_object(questionnaire.answers, Symptoms),
            IKDC.SPORTS_ACTIVITY: self._build_nested_object(
                questionnaire.answers, SportsActivity
            ),
            IKDC.KNEE_FUNCTION: self._build_nested_object(
                questionnaire.answers, KneeFunction
            ),
        }
        return IKDC.from_dict(ikdc_dict)

    def _build_nested_object(self, answers: list[QuestionnaireAnswer], cls):
        data = {
            field: answer.answerScore
            for field, question_id in cls.field_to_id_map().items()
            for answer in answers
            if answer.questionId == question_id
        }
        return cls.from_dict(data)

    def _add_score_to_answers(self, answers: list[QuestionnaireAnswer]):
        question_map = config_body_to_question_map(self.config.configBody)
        for answer in answers:
            score = self._get_answer_score(question_map.get(answer.questionId), answer)
            answer.answerScore = score

    def _get_answer_score(self, question, answer: QuestionnaireAnswer):
        question_format = question.get("format")
        if question_format == QuestionAnswerFormat.TEXTCHOICE.value:
            answer_score = self._get_answer_weight(question, answer)
        elif question_format == QuestionAnswerFormat.SCALE.value:
            # todo take out when value validation is done at questionaire level
            answer_score = str_to_int(answer.value)

        elif question_format == QuestionAnswerFormat.BOOLEAN.value:
            answer_score = 1 if answer.value else 0
        else:
            msg = f"The question {answer.questionId} doesn't have answer options configured with value"
            raise InvalidRequestException(msg)
        return answer_score

    def _validate_minimum_answers(self, answers: list):
        if len(answers) < self.minimumAnswered:
            raise NotAllRequiredQuestionsAnsweredException(
                message="Number of questions answered below the minimum required"
            )
