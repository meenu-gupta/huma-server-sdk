from typing import Optional
from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.primitives import Questionnaire, OARS
from extensions.module_result.models.primitives.primitive import Primitive
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
    QuestionnaireAnswer,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.questionnaires.oars_questionnaire_calculator import (
    OARSQuestionnaireCalculator,
)
from sdk.common.exceptions.exceptions import InvalidRequestException


class OARSModule(QuestionnaireModule):
    moduleId = "OARS"
    primitives = [Questionnaire, OARS]
    calculator = OARSQuestionnaireCalculator
    ragEnabled = True
    minimumAnswered = 12

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        if len(primitives) > 1:
            raise InvalidRequestException("Only one questionnaire can be submitted")

        questionnaire = primitives[0]
        if not isinstance(questionnaire, Questionnaire):
            raise InvalidRequestException("Only questionnaire can be submitted")

        self._validate_minimum_answers(questionnaire.answers)
        self._add_score_to_answers(questionnaire.answers)
        oars_data = {
            **questionnaire.to_dict(include_none=False),
            **{key: 0.0 for key in OARS.__annotations__.keys()},
        }
        oars = OARS.from_dict(oars_data)
        oars.scoring_answers = questionnaire.answers
        primitives.append(oars)
        return super().preprocess(primitives, user)

    def _validate_minimum_answers(self, answers: list):
        if len(answers) < self.minimumAnswered:
            raise NotAllRequiredQuestionsAnsweredException(
                message="Number of questions answered below the minimum required"
            )

    def _add_score_to_answers(self, answers: list[QuestionnaireAnswer]):
        question_map = config_body_to_question_map(self.config.configBody)
        invalid_answer_format = set()

        for answer in answers:
            question = question_map.get(question_id := answer.questionId)
            if question.get("format") != QuestionAnswerFormat.TEXTCHOICE.value:
                invalid_answer_format.add(question_id)
                continue
            answer.answerScore = self._get_answer_weight(question, answer)

        if invalid_answer_format:
            msg = f"The answer with question ids {','.join(invalid_answer_format)} have invlaid format"
            raise InvalidRequestException(msg)
        return answers
