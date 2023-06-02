import unittest

from sdk.common.utils.common_functions_utils import (
    escape,
    round_half_up,
    find_last_less_or_equal_element_index,
)


class MiscellaneousTestCase(unittest.TestCase):
    def test_escape(self):
        valid = "string"
        invalid = "string\\"
        escaped_invalid = "string\\\\"
        empty = ""

        self.assertEqual(escaped_invalid, escape(invalid))
        self.assertEqual(valid, escape(valid))
        self.assertEqual(empty, escape(empty))
        self.assertEqual(None, escape(None))

    def test_round_half_up(self):
        rounded = round_half_up(1.25, 1)
        self.assertEqual(1.3, rounded)

        rounded = round_half_up(1.25, 2)
        self.assertEqual(1.25, rounded)

        rounded = round_half_up(1.255, 2)
        self.assertEqual(1.26, rounded)

        rounded = round_half_up(1.35, 1)
        self.assertEqual(1.4, rounded)

        rounded = round_half_up(2.5)
        self.assertEqual(3, rounded)

    def test_find_last_less_or_equal_element_index(self):
        func = find_last_less_or_equal_element_index
        item = 5
        items = [1, 4, 5, 8]
        self.assertEqual(func(item, items), 2)

        items = [3, 4, 5]
        self.assertEqual(func(item, items), 2)

        items = [5, 10, 15, 20]
        self.assertEqual(func(item, items), 0)

        items = [1]
        self.assertEqual(func(item, items), 0)

        items = [10, 15, 20]
        self.assertEqual(func(item, items), -1)

        items = [10]
        self.assertEqual(func(item, items), -1)
