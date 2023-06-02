import unittest

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.versioning.router.versioning_requests import IncreaseVersionRequestObject


class IncreaseVersionRequestObjectTestCase(unittest.TestCase):
    @staticmethod
    def _sample_increase_version_req_obj():
        return {
            IncreaseVersionRequestObject.SERVER_VERSION: "34.6.4",
            IncreaseVersionRequestObject.API_VERSION: "v1",
        }

    def test_success_create_increase_version_req_obj(self):
        data = self._sample_increase_version_req_obj()
        try:
            IncreaseVersionRequestObject.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_increase_version_req_obj_validation_fails(self):
        data = self._sample_increase_version_req_obj()
        data[IncreaseVersionRequestObject.SERVER_VERSION] = "aa"
        with self.assertRaises(ConvertibleClassValidationError):
            IncreaseVersionRequestObject.from_dict(data)


if __name__ == "__main__":
    unittest.main()
