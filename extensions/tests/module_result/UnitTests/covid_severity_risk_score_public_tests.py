import unittest

from extensions.module_result.common.enums import (
    BiologicalSex,
    Ethnicity,
    SmokeStatus,
    BloodType,
    PreExistingCondition,
    CurrentSymptom,
)
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_covid19_severity_risk_score import (
    Covid19SeverityRiskScore,
)
from extensions.module_result.models.primitives.primitive_covid19_severity_risk_score_public import (
    Covid19SeverityRiskScorePublic,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


def _sample_data():
    return {
        **common_fields(),
        Primitive.USER_ID: SAMPLE_ID,
        Primitive.MODULE_ID: SAMPLE_ID,
        Covid19SeverityRiskScorePublic.AGE: 30,
        Covid19SeverityRiskScorePublic.WEIGHT: 65,
        Covid19SeverityRiskScorePublic.HEIGHT: 176,
        Covid19SeverityRiskScorePublic.BIOLOGICAL_SEX: BiologicalSex.MALE.value,
        Covid19SeverityRiskScorePublic.ETHNICITY: Ethnicity.WHITE.value,
        Covid19SeverityRiskScorePublic.SMOKE_STATUS: SmokeStatus.YES_AND_I_STILL_DO.value,
        Covid19SeverityRiskScorePublic.BLOOD_TYPE: BloodType.B_POSITIVE.value,
        Covid19SeverityRiskScorePublic.PRE_EXISTING_CONDITIONS: [
            PreExistingCondition.HEALTH_FAILURE.value
        ],
        Covid19SeverityRiskScorePublic.TEMPERATURE: 37.8,
        Covid19SeverityRiskScorePublic.CURRENT_SYMPTOMS: [
            CurrentSymptom.HEADACHE.value
        ],
        Covid19SeverityRiskScorePublic.HEART_RATE: 90,
        Covid19SeverityRiskScorePublic.RESTING_BREATH_RATE: 78,
        Covid19SeverityRiskScorePublic.OXYGEN_SATURATION: 87,
    }


class CovidSeverityScorePublicTestCase(unittest.TestCase):
    def test_success_create_covid_severity_public_primitive(self):
        data = _sample_data()
        try:
            Covid19SeverityRiskScorePublic.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_covid_severity_public__no_required_fields(self):
        required_fields = [
            Covid19SeverityRiskScorePublic.AGE,
            Covid19SeverityRiskScorePublic.HEIGHT,
            Covid19SeverityRiskScorePublic.BIOLOGICAL_SEX,
            Covid19SeverityRiskScorePublic.ETHNICITY,
            Covid19SeverityRiskScorePublic.SMOKE_STATUS,
            Covid19SeverityRiskScorePublic.BLOOD_TYPE,
            Covid19SeverityRiskScorePublic.PRE_EXISTING_CONDITIONS,
            Covid19SeverityRiskScorePublic.TEMPERATURE,
            Covid19SeverityRiskScorePublic.CURRENT_SYMPTOMS,
            Covid19SeverityRiskScorePublic.HEART_RATE,
            Covid19SeverityRiskScorePublic.RESTING_BREATH_RATE,
            Covid19SeverityRiskScorePublic.OXYGEN_SATURATION,
        ]
        for field in required_fields:
            data = _sample_data()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                Covid19SeverityRiskScorePublic.from_dict(data)


class CovidSeverityRiskScore(unittest.TestCase):
    @staticmethod
    def _sample_data():
        data = _sample_data()
        data[Covid19SeverityRiskScore.RESTING_HEART_RATE] = 65
        return data

    def test_success_create_covid_severity_primitive(self):
        data = self._sample_data()
        try:
            Covid19SeverityRiskScore.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_covid_severity__no_required_fields(self):
        required_fields = [
            Covid19SeverityRiskScore.AGE,
            Covid19SeverityRiskScore.HEIGHT,
            Covid19SeverityRiskScore.BIOLOGICAL_SEX,
            Covid19SeverityRiskScore.ETHNICITY,
            Covid19SeverityRiskScore.SMOKE_STATUS,
            Covid19SeverityRiskScore.BLOOD_TYPE,
            Covid19SeverityRiskScore.PRE_EXISTING_CONDITIONS,
            Covid19SeverityRiskScore.TEMPERATURE,
            Covid19SeverityRiskScore.CURRENT_SYMPTOMS,
            Covid19SeverityRiskScore.RESTING_BREATH_RATE,
            Covid19SeverityRiskScore.OXYGEN_SATURATION,
            Covid19SeverityRiskScore.RESTING_HEART_RATE,
        ]
        for field in required_fields:
            data = self._sample_data()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                Covid19SeverityRiskScore.from_dict(data)


if __name__ == "__main__":
    unittest.main()
