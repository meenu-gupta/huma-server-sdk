from unittest import TestCase

from extensions.common.s3object import FlatBufferS3Object
from extensions.module_result.models.primitives import Step
from extensions.tests.module_result.UnitTests.primitives_tests import COMMON_FIELDS


class StepTestCase(TestCase):

    EXPECTED_MULTIPLE_VALUES = [
        {
            "id": "5b5279d1e303d394db6ea0f8",
            "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 100},
            "d": "2019-06-30T00:00:00Z",
        },
        {
            "id": "5b5279d1e303d394db6ea134",
            "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 57.02},
            "d": "2019-06-30T01:00:00Z",
        },
    ]

    def test_success_creation_multiple_values(self):
        COMMON_FIELDS[Step.VALUE] = 90
        COMMON_FIELDS[Step.DATA_TYPE] = "MULTIPLE_VALUE"
        COMMON_FIELDS[Step.MULTIPLE_VALUES] = [
            {
                "id": "5b5279d1e303d394db6ea0f8",
                "h": {"0": 698},
                "d": "2019-06-30T00:00:00Z",
            },
            {
                "id": "5b5279d1e303d394db6ea134",
                "h": {"0": 690},
                "d": "2019-06-30T01:00:00Z",
            },
        ]
        COMMON_FIELDS[Step.RAW_DATA_OBJECT] = {
            FlatBufferS3Object.KEY: "sample",
            FlatBufferS3Object.BUCKET: "sample",
            FlatBufferS3Object.REGION: "sample",
            FlatBufferS3Object.FBS_VERSION: 1,
        }
        primitive = Step.create_from_dict(COMMON_FIELDS, name="Step")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.value, 90)
        self.assertEqual(primitive.dataType, Step.DataType.MULTIPLE_VALUE)

    def test_success_creation_multiple_values_backward_compatability(self):
        COMMON_FIELDS[Step.VALUE] = 90
        COMMON_FIELDS[Step.DATA_TYPE] = "MULTIPLE_VALUE"
        COMMON_FIELDS[Step.MULTIPLE_VALUES] = [
            {
                "id": "5b5279d1e303d394db6ea0f8",
                "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 100},
                "d": "2019-06-30T00:00:00Z",
            },
            {
                "id": "5b5279d1e303d394db6ea134",
                "p": {"0": 56.56, "15": 56.56, "30": 56.58, "45": 57.02},
                "d": "2019-06-30T01:00:00Z",
            },
        ]
        COMMON_FIELDS[Step.RAW_DATA_OBJECT] = {
            FlatBufferS3Object.KEY: "sample",
            FlatBufferS3Object.BUCKET: "sample",
            FlatBufferS3Object.REGION: "sample",
            FlatBufferS3Object.FBS_VERSION: 1,
        }

        primitive = Step.create_from_dict(COMMON_FIELDS, name="Step")
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.value, 90)
        self.assertEqual(primitive.dataType, Step.DataType.MULTIPLE_VALUE)
