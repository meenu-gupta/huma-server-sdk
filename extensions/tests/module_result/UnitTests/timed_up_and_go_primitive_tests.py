import unittest

from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_timed_upandgo import (
    TimedUpAndGo,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class TimedUpAndGoPrimitiveTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            TimedUpAndGo.VALUE: 0.3,
        }

    def test_success_create_timed_up_and_go_primitive(self):
        data = self._sample_data()
        try:
            TimedUpAndGo.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_timed_up_and_go_primitive__no_required_field(self):
        data = self._sample_data()
        data.pop(TimedUpAndGo.VALUE)
        with self.assertRaises(ConvertibleClassValidationError):
            TimedUpAndGo.from_dict(data)


if __name__ == "__main__":
    unittest.main()
