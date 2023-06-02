from typing import Any
from unittest import TestCase

from extensions.common.s3object import FlatBufferS3Object

from extensions.module_result.models.primitives import (
    BMI,
    HighFrequencyHeartRate,
    PeakFlow,
    Primitive,
)
from extensions.module_result.models.primitives import (
    ECGHealthKit,
    ECGReading,
)
from extensions.module_result.models.primitives.primitive_eq_5d_5l import EQ5D5L
from sdk.common.utils.convertible import ConvertibleClassValidationError


TEST_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_USER_ID = "5e8f0c74b50aa9656c34789a"
TEST_MODULE_ID = "5fe459311382397fd354701d"

COMMON_FIELDS: dict[str, Any] = {
    Primitive.USER_ID: TEST_USER_ID,
    Primitive.MODULE_ID: TEST_MODULE_ID,
    Primitive.DEPLOYMENT_ID: TEST_DEPLOYMENT_ID,
    Primitive.DEVICE_NAME: "iOS",
}


class PrimitiveTestCase(TestCase):
    def _assert_convertible_validation_err(self, cls, data: dict = None):
        if not data:
            data = COMMON_FIELDS
        with self.assertRaises(ConvertibleClassValidationError):
            cls.create_from_dict(data, name=cls.__name__)


class BMITestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 30
        primitive = BMI.create_from_dict(COMMON_FIELDS, name="BMI")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "kg/cm2")


class PeakFlowTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 300
        primitive = PeakFlow.create_from_dict(COMMON_FIELDS, name="PeakFlow")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.valueUnit, "L/s")

    def test_failed_value_validator_smaller_range(self):
        COMMON_FIELDS["value"] = 299
        self._assert_convertible_validation_err(PeakFlow)

    def test_failed_value_validator_greater_range(self):
        COMMON_FIELDS["value"] = 701
        self._assert_convertible_validation_err(PeakFlow)


class HighFrequencyTestCase(TestCase):
    def test_success_creation_single_value(self):
        COMMON_FIELDS["value"] = 90
        COMMON_FIELDS["dataType"] = "SINGLE_VALUE"
        primitive = HighFrequencyHeartRate.create_from_dict(
            COMMON_FIELDS, name="HighFrequencyHeartRate"
        )
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.value, 90)
        self.assertEqual(
            primitive.dataType, HighFrequencyHeartRate.DataType.SINGLE_VALUE
        )


class ECGTestCase(TestCase):
    def test_success_valid_data(self):
        COMMON_FIELDS["value"] = 3
        COMMON_FIELDS["ecgReading"] = {
            ECGReading.AVERAGE_HEART_RATE: 98.5,
            ECGReading.DATA_POINTS: {
                FlatBufferS3Object.KEY: "sample",
                FlatBufferS3Object.BUCKET: "sample",
                FlatBufferS3Object.REGION: "sample",
                FlatBufferS3Object.FBS_VERSION: 1,
            },
        }
        primitive = ECGHealthKit.create_from_dict(COMMON_FIELDS, name="ECGHealthKit")
        self.assertIsNotNone(primitive)

    def test_failure_out_of_acceptable_value(self):
        COMMON_FIELDS["value"] = 99
        COMMON_FIELDS["ecgReading"] = {
            ECGReading.AVERAGE_HEART_RATE: 98.5,
            ECGReading.DATA_POINTS: [123.5, 444.5],
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ECGHealthKit.create_from_dict(COMMON_FIELDS, name="ECGHealthKit")

    def test_failure_no_ecg_reading(self):
        COMMON_FIELDS["value"] = 3
        with self.assertRaises(ConvertibleClassValidationError):
            ECGHealthKit.create_from_dict(COMMON_FIELDS, name="ECGHealthKit")

    def test_failure_no_average_heart_rate(self):
        COMMON_FIELDS["value"] = 3
        COMMON_FIELDS["ecgReading"] = {
            ECGReading.DATA_POINTS: [123.5, 444.5],
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ECGHealthKit.create_from_dict(COMMON_FIELDS, name="ECGHealthKit")

    def test_failure_no_data_points(self):
        COMMON_FIELDS["value"] = 3
        COMMON_FIELDS["ecgReading"] = {
            ECGReading.AVERAGE_HEART_RATE: 98.5,
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ECGHealthKit.create_from_dict(COMMON_FIELDS, name="ECGHealthKit")

    def test_failure_not_acceptable_classification_enum(self):
        invalid_enums = [5, 7]
        for value in invalid_enums:
            COMMON_FIELDS["value"] = value
            COMMON_FIELDS["ecgReading"] = {
                ECGReading.AVERAGE_HEART_RATE: 98.5,
                ECGReading.DATA_POINTS: [123.5, 444.5],
            }
            with self.assertRaises(ConvertibleClassValidationError):
                ECGHealthKit.create_from_dict(COMMON_FIELDS, name="ECGHealthKit")


class EQ5D5LTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        COMMON_FIELDS[EQ5D5L.INDEX_VALUE] = 30.0
        COMMON_FIELDS[EQ5D5L.HEALTH_STATE] = 3
        COMMON_FIELDS[EQ5D5L.ANXIETY] = 2
        COMMON_FIELDS[EQ5D5L.PAIN] = 1
        COMMON_FIELDS[EQ5D5L.SELF_CARE] = 5
        COMMON_FIELDS[EQ5D5L.USUAL_ACTIVITIES] = 3
        COMMON_FIELDS[EQ5D5L.SELF_CARE] = 4
        COMMON_FIELDS[EQ5D5L.EQ_VAS] = 50

        primitive = EQ5D5L.create_from_dict(COMMON_FIELDS, name="EQ5D5L")
        self.assertIsNotNone(primitive)

    def test_failure_invalid_value(self):
        COMMON_FIELDS[EQ5D5L.INDEX_VALUE] = "read"
        with self.assertRaises(ConvertibleClassValidationError):
            ECGHealthKit.create_from_dict(COMMON_FIELDS, name="EQ5D5L")
