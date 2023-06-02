from unittest import TestCase

from sdk.common.requests.request_utils import RequestContext


class RequestObjectTestCase(TestCase):
    test_value = 5

    def setUp(self) -> None:
        self.request_object = RequestContext()

    def test_attribute_creation(self):
        self.request_object.new_value = self.test_value

        self.assertEqual(self.request_object.new_value, self.test_value)

    def test_read_non_existent_attribute_raises_error(self):
        with self.assertRaises(AttributeError):
            _ = self.request_object.new_value

    def test_delete_attribute(self):
        self.request_object.new_value = self.test_value

        del self.request_object.new_value
        with self.assertRaises(AttributeError):
            _ = self.request_object.new_value

    def test_delete_non_existent_attribute_raises_error(self):
        with self.assertRaises(AttributeError):
            del self.request_object.new_value

    def test_contains_attribute(self):
        self.request_object.new_value = self.test_value

        self.assertEqual("new_value" in self.request_object, True)
        self.assertEqual("non_existent" in self.request_object, False)

    def test_get_existent_attribute(self):
        self.request_object.new_value = self.test_value

        self.assertEqual(self.request_object.get("new_value"), self.test_value)

    def test_get_none_existent_attribute(self):
        self.assertEqual(self.request_object.get("new_value"), None)
