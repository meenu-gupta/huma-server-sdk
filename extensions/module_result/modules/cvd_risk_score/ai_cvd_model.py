from collections import defaultdict
from enum import Enum
from typing import Any

from extensions.module_result.common.enums import BiologicalSex
from extensions.module_result.models.primitives.cvd_risk_score import CVDRiskScore
from extensions.module_result.modules.cvd_risk_score._config import (
    CVDRiskScoreConfig,
    QuestionConfig,
)
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, meta
from sdk.common.utils.validators import validate_entity_name


class CVDRiskScoreRequestObject(dict):
    def __init__(self, config: CVDRiskScoreConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    @classmethod
    def from_primitive(cls, primitive: CVDRiskScore, config: CVDRiskScoreConfig = None):
        obj = cls(config or CVDRiskScoreConfig())
        obj.update(obj.build_gender_score_dict(primitive.sex))

        for field, user_answer in primitive.items():
            obj.update(obj.build_score_dict(field, user_answer))

        return cls._convert_enums(obj)

    def build_age_score_dict(self, age: float):
        answer_config = self.config.cvd_age.match_answer(age)
        return {self.config.cvd_age.targetField: answer_config.value}

    def build_gender_score_dict(self, gender: BiologicalSex):
        answer_config = self.config.cvd_sex.match_answer(gender)
        return {self.config.cvd_sex.targetField: answer_config.value}

    def build_score_dict(self, field: str, user_answer: Any):
        question_config = self.config.find(lambda c: c.primitiveField == field)

        if not question_config:
            return {}

        if not question_config.answers:
            return {question_config.targetField: user_answer}

        return self._build_score_dict(question_config, user_answer)

    def _build_score_dict(self, config: QuestionConfig, user_answer):
        types = CVDRiskScoreConfig.AnswerType
        if config.answerType != types.MULTIPLE:
            return self._build_score_based_on_user_answer(config, user_answer)

        mapping = defaultdict(list)
        for option in user_answer:
            field_score = self._build_score_based_on_user_answer(config, option)
            for key, value in field_score.items():
                mapping[key].append(value)

        return mapping

    @staticmethod
    def _build_score_based_on_user_answer(config: QuestionConfig, user_answer) -> dict:
        answer = config.match_answer(user_answer)
        target_field = config.targetField or answer.targetField

        if not any((answer, target_field)):
            return {}

        return {target_field: answer.value}

    @staticmethod
    def _convert_enums(data: dict[str, Any]) -> dict[str, Any]:
        for key, val in data.items():
            if isinstance(val, Enum):
                data[key] = val.value
            elif isinstance(val, list):
                data[key] = [v.value for v in val if isinstance(v, Enum)]

        return data


@convertibleclass
class AIRiskFactor:
    contribution: float = required_field()
    label: str = required_field(metadata=meta(validate_entity_name))


@convertibleclass
class AIRiskTrajectory:
    risk: float = required_field()
    days: float = required_field()


@convertibleclass
class CVDRiskScoreResponseObject:
    risk: float = required_field()
    riskFactors: list[AIRiskFactor] = required_field()
    riskTrajectory: list[AIRiskTrajectory] = required_field()
