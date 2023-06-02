from unittest import TestCase

from extensions.module_result.models.primitives.cvd_risk_score import (
    RiskFactor,
    CVDRiskScore,
    RiskLabel,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


def cvd_sample():
    return {
        "userId": "5e8f0c74b50aa9656c34789c",
        "moduleId": "CVDRiskScore",
        "moduleConfigId": "613bb279d393b8b116d65d22",
        "deploymentId": "5d386cc6ff885918d96edb2c",
        "version": 0,
        "deviceName": "iOS",
        "isAggregated": False,
        "startDateTime": "2021-10-19T18:27:26.785788Z",
        "submitterId": "5e8f0c74b50aa9656c34789c",
        "age": 33.0,
        "sex": "MALE",
        "alcoholIntake": "SPECIAL_OCCASIONS",
        "sleepDuration": 7.0,
        "smokingStatus": True,
        "walkingPace": "BRISK_PACE",
        "overallHealth": "GOOD",
        "existingConditions": ["DIABETES", "HIGH_BLOOD_PRESSURE"],
        "existingSymptoms": ["ABDOMINAL_AND_PELVIC_PAIN"],
        "currentMedications": [
            "CHOLESTEROL_LOWERING_MEDICATION",
            "BLOOD_PRESSURE_MEDICATION",
        ],
        "familyHeartDisease": ["MOTHER", "SIBLING"],
        "heartRate": 95.0,
        "waistCircumference": 90.0,
        "hipCircumference": 90.0,
        "waistToHipRatio": 1.0,
    }


class CVDRiskScorePrimitiveTestCase(TestCase):
    def test_risk_factor_color_hex__protective(self):
        data = {
            RiskFactor.CONTRIBUTION: 0.1,
            RiskFactor.NAME: RiskLabel.BODY_MEASUREMENTS,
        }
        factor = RiskFactor.from_dict(data)
        self.assertEqual(RiskFactor.RISK_COLOR, factor.colorHex)

    def test_risk_factor_color_hex__risk(self):
        data = {
            RiskFactor.CONTRIBUTION: -0.1,
            RiskFactor.NAME: RiskLabel.BODY_MEASUREMENTS,
        }
        factor: RiskFactor = RiskFactor.from_dict(data)
        self.assertEqual(RiskFactor.PROTECTIVE_COLOR, factor.colorHex)

    def test_build_cvd_risk_score_wrong_heart_rate(self):
        value_outside_range = 2
        data = {
            **cvd_sample(),
            CVDRiskScore.HEART_RATE: value_outside_range,
        }
        with self.assertRaises(ConvertibleClassValidationError) as error:
            CVDRiskScore.from_dict(data)
        self.assertErrorFor(CVDRiskScore.HEART_RATE, error)

    def test_build_cvd_risk_score_wrong_waist_circumference(self):
        value_outside_range = 501
        data = {
            **cvd_sample(),
            CVDRiskScore.WAIST_CIRCUMFERENCE: value_outside_range,
        }
        with self.assertRaises(ConvertibleClassValidationError) as error:
            CVDRiskScore.from_dict(data)
        self.assertErrorFor(CVDRiskScore.WAIST_CIRCUMFERENCE, error)

    def test_build_cvd_risk_score_wrong_hip_circumference(self):
        value_outside_range = 501
        data = {
            **cvd_sample(),
            CVDRiskScore.HIP_CIRCUMFERENCE: value_outside_range,
        }
        with self.assertRaises(ConvertibleClassValidationError) as error:
            CVDRiskScore.from_dict(data)
        self.assertErrorFor(CVDRiskScore.HIP_CIRCUMFERENCE, error)

    def test_build_cvd_risk_score_wrong_sleep_duration(self):
        value_outside_range = 13
        data = {
            **cvd_sample(),
            CVDRiskScore.SLEEP_DURATION: value_outside_range,
        }
        with self.assertRaises(ConvertibleClassValidationError) as error:
            CVDRiskScore.from_dict(data)
        self.assertErrorFor(CVDRiskScore.SLEEP_DURATION, error)

    def assertErrorFor(self, field_name: str, error):
        self.assertIn(field_name, error.exception.debug_message)
