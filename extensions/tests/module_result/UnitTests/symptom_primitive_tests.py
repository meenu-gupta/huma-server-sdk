import unittest

from extensions.module_result.models.primitives import Symptom, Primitive
from extensions.tests.module_result.IntegrationTests.test_samples import sample_symptom
from extensions.tests.module_result.UnitTests.primitives_tests import (
    TEST_USER_ID,
    TEST_DEPLOYMENT_ID,
    TEST_MODULE_ID,
    PrimitiveTestCase,
)


def _get_payload(data: dict):
    return {
        Primitive.USER_ID: TEST_USER_ID,
        Primitive.MODULE_ID: TEST_MODULE_ID,
        Primitive.DEPLOYMENT_ID: TEST_DEPLOYMENT_ID,
        Primitive.DEVICE_NAME: "iOS",
        **data,
    }


class SymptomPrimitiveTestCase(PrimitiveTestCase):
    def test_success_creation(self):
        data = _get_payload(data=sample_symptom())
        primitive = Symptom.create_from_dict(data, name=Symptom.__name__)
        self.assertIsNotNone(primitive)


if __name__ == "__main__":
    unittest.main()
