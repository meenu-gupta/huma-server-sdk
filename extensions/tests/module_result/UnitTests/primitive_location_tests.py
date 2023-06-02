import unittest

from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_location import Location
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class PrimitiveLocationTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            Location.LOCATION_PROVIDER: Location.LocationProviderType.DATAHUB.value,
            Location.LOCATION_QUESTION: Location.LocationQuestionType.WHERE_LIVING.value,
        }

    def test_success_create_location_primitive(self):
        data = self._sample_data()
        try:
            Location.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_location__no_required_fields(self):
        required_fields = [
            Location.LOCATION_PROVIDER,
            Location.LOCATION_QUESTION,
        ]
        for field in required_fields:
            data = self._sample_data()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                Location.from_dict(data)


if __name__ == "__main__":
    unittest.main()
