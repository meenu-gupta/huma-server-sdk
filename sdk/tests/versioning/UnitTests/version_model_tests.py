import copy
import unittest

from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.versioning.models.version import Version


class VersionModelTestCase(unittest.TestCase):
    def test_success_version_creation(self):
        try:
            Version.from_dict({Version.SERVER: "1.17.1", Version.API: "v2"})
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_used_wrong_type(self):
        data = {Version.SERVER: "huma.com", Version.API: "v2"}
        for key in data:
            copy_data = copy.deepcopy(data)
            with self.assertRaises(ConvertibleClassValidationError):
                copy_data[key] = 111
                Version.from_dict(copy_data)


if __name__ == "__main__":
    unittest.main()
