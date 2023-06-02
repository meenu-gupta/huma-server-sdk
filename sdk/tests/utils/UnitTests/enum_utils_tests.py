import unittest
from enum import Enum, IntEnum

from sdk.common.utils.enum_utils import enum_values


class EnumUtilsTestCase(unittest.TestCase):
    def test_enum_values(self):
        class TestEnum(Enum):
            a = "a"
            b = "b"

        self.assertEqual(enum_values(TestEnum), ["a", "b"])

        class TestIntEnum(IntEnum):
            a = 1
            b = 2

        self.assertEqual(enum_values(TestIntEnum), [1, 2])


if __name__ == "__main__":
    unittest.main()
