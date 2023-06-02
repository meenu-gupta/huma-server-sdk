import unittest

from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_checkin import Checkin
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class CheckInTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            Checkin.VALUE: "some_value",
        }

    def test_success_create_checkin_primitive(self):
        data = self._sample_data()
        try:
            Checkin.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_checkin__no_required_fields(self):
        data = self._sample_data()
        data.pop(Checkin.VALUE)
        with self.assertRaises(ConvertibleClassValidationError):
            Checkin.from_dict(data)


if __name__ == "__main__":
    unittest.main()
