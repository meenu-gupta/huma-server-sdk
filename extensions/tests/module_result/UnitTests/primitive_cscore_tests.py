import unittest

from extensions.module_result.models.primitives import Primitive
from extensions.module_result.models.primitives.primitive_cscore import CScore
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "61724a9675a276cff9ac72c7"


class CScorePrimitiveTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            CScore.VALUE: 176,
        }

    def test_success_create_cscore_primitive(self):
        data = self._sample_data()
        try:
            CScore.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()


if __name__ == "__main__":
    unittest.main()
