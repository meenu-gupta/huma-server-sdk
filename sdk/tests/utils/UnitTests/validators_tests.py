from datetime import datetime
import unittest
from copy import deepcopy

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import (
    remove_none_values,
    utc_str_val_to_field,
    utc_str_to_date,
    utc_str_field_to_val,
    utc_date_to_str,
)


class ValidatorsTestCase(unittest.TestCase):
    TEST_DICT_NO_NONE = {
        "a": {"b": "c", "d": "e", "f": 42},
        "g": {
            "b": "c",
            "d": "e",
            "f": 42,
            "h": [1, 2, 3, 4],
            "i": [{"j": "k", "l": "m"}, {"n": "o", "p": "q"}, {"d": (1, 2)}],
        },
        "r": (5, 6, 7, 8),
        "s": {"t", 9},
    }

    TEST_DICT_NONE = {
        "a": {"b": "c", "d": "e", "f": 42},
        "g": {
            "b": "c",
            "d": "e",
            "f": 42,
            "h": [1, 2, None, 3, 4],
            "i": [
                {"j": "k", "l": "m", "n": None},
                {"n": "o", "p": "q", "r": None},
                {"d": (1, 2, None)},
            ],
            "n": None,
        },
        "d": None,
        "r": (5, 6, 7, None, 8),
        "s": {"t", 9},
    }

    def test_small_dict_no_remove(self):
        test_dict = {"a": {"b": "c"}}
        test_dict_copy = deepcopy(test_dict)
        result_dict = remove_none_values(test_dict)

        self.assertTrue(result_dict == test_dict_copy)

    def test_small_dict_remove(self):
        test_dict = {"a": {"b": "c", "d": None}}
        expected_result = {"a": {"b": "c"}}
        result_dict = remove_none_values(test_dict)

        self.assertTrue(result_dict == expected_result)

    def test_small_dict_ignore_keys(self):
        test_dict = {"a": {"b": "c", "d": None}}
        test_dict_copy = deepcopy(test_dict)
        result_dict = remove_none_values(test_dict, {"d", "e"})
        self.assertTrue(result_dict == test_dict_copy)

    def test_creating_deepcopy(self):
        test_data = deepcopy(self.TEST_DICT_NO_NONE)
        result = remove_none_values(test_data)
        self.assertTrue(test_data == result)
        key = "new key"
        self.assertTrue(key not in test_data)
        result[key] = "new value"
        self.assertTrue(key not in test_data)

    def test_small_dict_different_ignore_keys(self):
        test_dict = {1: {2: None}}
        self.assertTrue(remove_none_values(test_dict) == {1: dict()})
        self.assertTrue(remove_none_values(test_dict, {1}) != test_dict)
        self.assertTrue(remove_none_values(test_dict, {2}) == test_dict)

    def test_dict_no_remove(self):
        test_dict = deepcopy(self.TEST_DICT_NO_NONE)
        result_dict = remove_none_values(test_dict, ignore_keys={"d"})
        self.assertTrue(result_dict == self.TEST_DICT_NO_NONE)

    def test_dict_remove(self):
        test_dict = deepcopy(self.TEST_DICT_NONE)
        result_dict = remove_none_values(test_dict)
        self.assertTrue(result_dict == self.TEST_DICT_NO_NONE)

    def test_utc_str_val_to_field(self):
        utc_str_val_to_field("2021-12-29T15:37:17.038Z")
        utc_str_val_to_field("2021-12-07T18:29:33Z")
        utc_str_to_date(datetime.utcnow())

        date_str = "2022-12-01T20:45"
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_val_to_field(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

        date_str = "2021-12-07T18:29Z"
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_val_to_field(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

        date_str = None
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_val_to_field(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

    def test_utc_str_to_date(self):
        utc_str_to_date("2021-12-29T15:37:17.038Z")
        utc_str_to_date("2021-12-07T18:29:33Z")
        utc_str_to_date(datetime.utcnow())

        date_str = "2021-12-"
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_to_date(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

        date_str = None
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_to_date(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

    def test_utc_str_field_to_val(self):
        utc_str_field_to_val(datetime.utcnow())

        date_str = None
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_field_to_val(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

        date_str = {}
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_str_field_to_val(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")

    def test_utc_date_to_str(self):
        utc_date_to_str(datetime.utcnow())

        date_str = None
        with self.assertRaises(ConvertibleClassValidationError) as e:
            utc_date_to_str(date_str)
        self.assertEqual(e.exception.__str__(), f"{date_str} is invalid date format")


if __name__ == "__main__":
    unittest.main()
