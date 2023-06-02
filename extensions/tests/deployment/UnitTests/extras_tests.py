import unittest

from bson import ObjectId

from sdk.common.utils.validators import id_as_obj_id

TEST_ID = "5d386cc6ff885918d96edb2c"


class IdToObjIdTestCase(unittest.TestCase):
    def test_converts_id_with_kwarg(self):
        class TestRepo:
            def __init__(self, test_case):
                self.test_case = test_case

            @id_as_obj_id
            def test_func(self, test_id):
                self.test_case.assertEqual(type(test_id), ObjectId)

        TestRepo(self).test_func(test_id=TEST_ID)

    def test_not_converts_param(self):
        class TestRepo:
            def __init__(self, test_case):
                self.test_case = test_case

            @id_as_obj_id
            def test_func(self, test_str):
                self.test_case.assertEqual(type(test_str), str)

        TestRepo(self).test_func(test_str=TEST_ID)

    def test_raises_error_pos_arg(self):
        class TestRepo:
            def __init__(self, test_case):
                self.test_case = test_case

            @id_as_obj_id
            def test_func(self, test_str):
                pass

        with self.assertRaises(TypeError):
            TestRepo(self).test_func(TEST_ID)
