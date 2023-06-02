import abc
from abc import ABC

from extensions.module_result.modules.module import Module, AzModuleMixin
from extensions.module_result.models.primitives import (
    PROMISGlobalHealth,
    Primitive,
    QuestionnaireAppResultValue,
    QuestionnaireAppResult,
)


class Calculator(ABC):
    T_SCORE_TABLE: dict

    class TScoreValueType:
        STD_ERR_FLOAT = "STD_ERR_FLOAT"
        VALUE_FLOAT = "VALUE_FLOAT"

        LABEL_MAP = {VALUE_FLOAT: "raw sum", STD_ERR_FLOAT: "std error float"}

    def build_standard_error_result(self, value) -> dict:
        label = self.TScoreValueType.LABEL_MAP[self.TScoreValueType.STD_ERR_FLOAT]
        return {
            QuestionnaireAppResultValue.LABEL: label,
            QuestionnaireAppResultValue.VALUE_TYPE: self.TScoreValueType.STD_ERR_FLOAT,
            QuestionnaireAppResultValue.VALUE_FLOAT: value,
        }

    def build_value_result(self, value) -> dict:
        label = self.TScoreValueType.LABEL_MAP[self.TScoreValueType.VALUE_FLOAT]
        return {
            QuestionnaireAppResultValue.LABEL: label,
            QuestionnaireAppResultValue.VALUE_TYPE: self.TScoreValueType.VALUE_FLOAT,
            QuestionnaireAppResultValue.VALUE_FLOAT: value,
        }

    def build_result(self, score: int, error_value: float):
        app_type = (
            QuestionnaireAppResult.QuestionnaireAppResultType.T_DISTRIBUTION.value
        )
        values = [
            self.build_standard_error_result(error_value),
            self.build_value_result(score),
        ]
        data = {
            QuestionnaireAppResult.APP_TYPE: app_type,
            QuestionnaireAppResult.VALUES: values,
        }
        return QuestionnaireAppResult.from_dict(data)

    def get_t_score_and_error(self, value: int) -> tuple[float, float]:
        return self.T_SCORE_TABLE[value]

    @abc.abstractmethod
    def calculate_raw_score(self, primitive: PROMISGlobalHealth):
        raise NotImplementedError


class GlobalMentalHealthCalculator(Calculator):
    T_SCORE_TABLE = {
        4: [21.2, 4.6],
        5: [25.1, 4.1],
        6: [28.4, 3.9],
        7: [31.3, 3.7],
        8: [33.8, 3.7],
        9: [36.3, 3.7],
        10: [38.8, 3.6],
        11: [41.1, 3.6],
        12: [43.5, 3.6],
        13: [45.8, 3.6],
        14: [48.3, 3.7],
        15: [50.8, 3.7],
        16: [53.3, 3.7],
        17: [56.0, 3.8],
        18: [59.0, 3.9],
        19: [62.5, 4.2],
        20: [67.6, 5.3],
    }

    def calculate_raw_score(self, primitive: PROMISGlobalHealth):
        return (
            primitive.global02.value
            + primitive.global04.value
            + primitive.global05
            + primitive.global10r.value
        )


class GlobalPhysicalHealthCalculator(Calculator):
    T_SCORE_TABLE = {
        4: [16.2, 4.8],
        5: [19.9, 4.7],
        6: [23.5, 4.5],
        7: [26.7, 4.3],
        8: [29.6, 4.2],
        9: [32.4, 4.2],
        10: [34.9, 4.1],
        11: [37.4, 4.1],
        12: [39.8, 4.1],
        13: [42.3, 4.2],
        14: [44.9, 4.3],
        15: [47.7, 4.4],
        16: [50.8, 4.6],
        17: [54.1, 4.7],
        18: [57.7, 4.9],
        19: [61.9, 5.2],
        20: [67.7, 5.9],
    }

    def calculate_raw_score(self, primitive: PROMISGlobalHealth):
        return (
            primitive.global03.value
            + primitive.global06.value
            + primitive.global07rc
            + primitive.global08r.value
        )


class PROMISGlobalHealthModule(AzModuleMixin, Module):
    moduleId = "PROMISGlobalHealth"
    primitives = [PROMISGlobalHealth]
    ragEnabled = True

    GLOBAL_7_SCORE_TABLE = [5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 1]

    def calculate(self, primitive: Primitive):
        if not isinstance(primitive, PROMISGlobalHealth):
            return

        primitive.global07rc = self._calculate_global_7_score(primitive.global07rc)
        self._calculate_mental_health_score(primitive)
        self._calculate_physical_health_score(primitive)

    @staticmethod
    def _calculate_mental_health_score(primitive: PROMISGlobalHealth):
        mental_calculator = GlobalMentalHealthCalculator()
        score = mental_calculator.calculate_raw_score(primitive)
        t_score, error = mental_calculator.get_t_score_and_error(score)
        mental_health = mental_calculator.build_result(score, error)
        primitive.mentalHealthResult = mental_health
        primitive.mentalHealthValue = t_score

    @staticmethod
    def _calculate_physical_health_score(primitive: PROMISGlobalHealth):
        physical_calculator = GlobalPhysicalHealthCalculator()
        score = physical_calculator.calculate_raw_score(primitive)
        t_score, error = physical_calculator.get_t_score_and_error(score)
        physical_health = physical_calculator.build_result(score, error)
        primitive.physicalHealthResult = physical_health
        primitive.physicalHealthValue = t_score

    def _calculate_global_7_score(self, value: int):
        return self.GLOBAL_7_SCORE_TABLE[value]
