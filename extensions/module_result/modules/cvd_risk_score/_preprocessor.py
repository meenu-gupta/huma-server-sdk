from extensions.authorization.models.user import User
from extensions.module_result.exceptions import NotAllRequiredQuestionsAnsweredException
from extensions.module_result.models.primitives import (
    CVDRiskScore,
    Primitive,
    Questionnaire,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
)
from ._config import CVDRiskScoreConfig, QuestionConfig


class CVDRiskScorePreprocessor:
    def __init__(self, user: User):
        self.user = user
        if not self.user.dateOfBirth:
            raise NotAllRequiredQuestionsAnsweredException(
                "User doesn't have dateOfBirth set"
            )

        self.config = CVDRiskScoreConfig()

    def run(self, primitives: list[Primitive]):
        """Appends CVDRiskScore primitives generated from Questionnaires"""
        questionnaires = self._filter_questionnaires(primitives)
        primitives.extend([self.build_cvd_risk_score(q) for q in questionnaires])

    def build_cvd_risk_score(self, primitive: Questionnaire):
        cvd_data = {
            **primitive.to_dict(include_none=False),
            CVDRiskScore.AGE: self.user.get_age(),
            CVDRiskScore.SEX: self.user.biologicalSex and self.user.biologicalSex.name,
        }

        for answer_obj in primitive.answers:
            answer_value = self._process_answer_obj(answer_obj)

            question_config = self.config.get(answer_obj.questionId)
            if not question_config:
                continue

            new_data = {question_config.primitiveField: answer_value}

            if question_config.primitiveField == CVDRiskScore.WAIST_TO_HIP_RATIO:
                new_data = answer_value

            cvd_data.update(new_data)

        return CVDRiskScore.from_dict(cvd_data)

    @staticmethod
    def _filter_questionnaires(primitives: list[Primitive]) -> list[Questionnaire]:
        return [p for p in primitives if isinstance(p, Questionnaire)]

    def _process_answer_obj(self, answer: QuestionnaireAnswer):
        answer_value = answer.get_answer()
        if answer.format == QuestionAnswerFormat.TEXTCHOICE:
            return self._process_text_choice(
                config=self.config.get(answer.questionId),
                answers=answer.selectedChoices,
            )
        return answer_value

    @staticmethod
    def _process_text_choice(config: QuestionConfig, answers: list[str]):
        for answer in config.answers:
            if answer.exclusive and answer.text in answers:
                return [answer.text]

        if config.answerType == CVDRiskScoreConfig.AnswerType.SINGLE:
            return answers[0]

        return answers
