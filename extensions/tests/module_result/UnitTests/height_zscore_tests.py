import unittest

from extensions.module_result.models.primitives import Height
from extensions.tests.module_result.UnitTests.primitives_tests import COMMON_FIELDS
from sdk.common.utils.convertible import ConvertibleClassValidationError


class HeightZScoreTestCase(unittest.TestCase):
    def test_success_creation(self):
        COMMON_FIELDS["value"] = 101
        primitive = Height.create_from_dict(COMMON_FIELDS, name="Height")
        self.assertIsNotNone(primitive)

    def test_failure_out_of_allowed_range(self):
        with self.assertRaises(ConvertibleClassValidationError):
            COMMON_FIELDS["value"] = 99
            Height.create_from_dict(COMMON_FIELDS, name="Height")

        with self.assertRaises(ConvertibleClassValidationError):
            COMMON_FIELDS["value"] = 251
            Height.create_from_dict(COMMON_FIELDS, name="Height")


if __name__ == "__main__":
    unittest.main()
