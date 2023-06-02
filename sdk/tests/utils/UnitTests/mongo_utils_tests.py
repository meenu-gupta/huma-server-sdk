import unittest
from unittest.mock import MagicMock
from bson import ObjectId

from sdk.common.adapter.mongodb.mongodb_utils import (
    kwargs_to_obj_id,
    convert_mongo_comparison_operators,
    db_is_accessible,
)
from sdk.common.constants import LESS_OR_EQUAL_TO, VALUE_IN


class MockAccessibleDB:
    instance = MagicMock()
    command = MagicMock(return_value={"ok": 1.0})


class MockUnAccessibleDB:
    instance = MagicMock()
    command = MagicMock(return_value={"ok": 0.0})


class MongoUtilsTestCase(unittest.TestCase):
    def test_success_convert_mongo_comparison_operators(self):
        sample_data = {LESS_OR_EQUAL_TO: 5, "nested_item": {VALUE_IN: [1, 2, 3]}}
        res = convert_mongo_comparison_operators(sample_data)
        expected_result = {"$lte": 5, "nested_item": {"$in": [1, 2, 3]}}
        self.assertEqual(res, expected_result)

    def test_success_id_convertion_in_kwargs_to_obj_id(self):
        sample_data = {"someId": {"$in": ["60c869952fba04941f6aaec0"]}}
        res = kwargs_to_obj_id(sample_data)
        self.assertTrue(isinstance(res["someId"]["$in"][0], ObjectId))

        sample_data = {"someId": {VALUE_IN: ["60c869952fba04941f6aaec0"]}}
        res = kwargs_to_obj_id(sample_data)
        self.assertTrue(isinstance(res["someId"][VALUE_IN][0], ObjectId))

    def test_success_db_is_accessible(self):
        res = db_is_accessible(MockAccessibleDB())
        self.assertTrue(res)

    def test_failure_db_is_unaccessible(self):
        res = db_is_accessible(MockUnAccessibleDB())
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
