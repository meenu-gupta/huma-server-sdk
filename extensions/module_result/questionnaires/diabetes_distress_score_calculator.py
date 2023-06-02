from extensions.module_result.models.primitives import (
    Primitive,
    DiabetesDistressScore,
    QuestionnaireAnswer,
)
from sdk.common.exceptions.exceptions import InvalidRequestException


class DiabetesDistressScoreCalculator:
    def calculate(self, primitive: Primitive, answers: list[QuestionnaireAnswer]):
        if isinstance(primitive, DiabetesDistressScore):
            dds_data = self._calculate_diabetes_distress_score(answers)
            for key, value in dds_data.items():
                primitive.set_field_value(key, value)

    def _calculate_diabetes_distress_score(
        self,
        answers: list[QuestionnaireAnswer],
    ) -> dict[str, float]:
        scoring = {
            "Not a problem": 1,
            "A slight problem": 2,
            "A moderate problem": 3,
            "Somewhat serious problem": 4,
            "A serious problem": 5,
            "A very serious problem": 6,
        }

        # DDS-2 calculations
        if len(answers) == 2:
            return self.calculate_dds2(answers, scoring)
        # DDS-17 calculations
        elif len(answers) == 19:
            return self.calculate_dds17(answers, scoring)
        else:
            raise InvalidRequestException("Incorrect amount of answers")

    def calculate_dds2(
        self, answers: list[QuestionnaireAnswer], scoring: dict
    ) -> dict[str, float]:
        dds_dict = {}
        total_scores_sum = 0
        for answer_object in answers:
            score = scoring.get(answer_object.answerText, None)
            if score is None:
                raise InvalidRequestException(
                    f'Invalid answer "{answer_object.answerText}" for question "{answer_object.question}"'
                )
            total_scores_sum += score
        dds_dict[DiabetesDistressScore.TOTAL_DDS] = round(total_scores_sum / 2, 2)
        return dds_dict

    def calculate_dds17(
        self, answers: list[QuestionnaireAnswer], scoring: dict
    ) -> dict[str, float]:
        # preparing data for calculations, indexes are based on 17 questions
        emotional_burden_indexes = [1, 3, 8, 11, 14]
        physician_distress_indexes = [2, 4, 9, 15]
        regimen_distress_indexes = [5, 6, 10, 12, 16]
        interpersonal_distress_indexes = [7, 13, 17]

        emotional_burden_scores_sum = 0
        physician_distress_scores_sum = 0
        regimen_distress_scores_sum = 0
        interpersonal_distress_scores_sum = 0
        total_scores_sum = 0
        dds_dict = {}

        # skipping screening questions
        for index, answer_object in enumerate(answers[2:], start=1):

            score = scoring.get(answer_object.answerText, None)
            if score is None:
                raise InvalidRequestException(
                    f'Invalid answer "{answer_object.answerText}" for question "{answer_object.question}"'
                )
            total_scores_sum += score

            # summing emotional burden scores
            if index in emotional_burden_indexes:
                emotional_burden_scores_sum += score
            if index in physician_distress_indexes:
                physician_distress_scores_sum += score
            if index in regimen_distress_indexes:
                regimen_distress_scores_sum += score
            if index in interpersonal_distress_indexes:
                interpersonal_distress_scores_sum += score

        # calculating scores
        dds_dict[DiabetesDistressScore.TOTAL_DDS] = round(total_scores_sum / 17, 2)
        dds_dict[DiabetesDistressScore.EMOTIONAL_BURDEN] = round(
            emotional_burden_scores_sum / len(emotional_burden_indexes), 2
        )
        dds_dict[DiabetesDistressScore.PHYSICIAN_DISTRESS] = round(
            physician_distress_scores_sum / len(physician_distress_indexes), 2
        )
        dds_dict[DiabetesDistressScore.REGIMEN_DISTRESS] = round(
            regimen_distress_scores_sum / len(regimen_distress_indexes), 2
        )
        dds_dict[DiabetesDistressScore.INTERPERSONAL_DISTRESS] = round(
            interpersonal_distress_scores_sum / len(interpersonal_distress_indexes), 2
        )
        return dds_dict
