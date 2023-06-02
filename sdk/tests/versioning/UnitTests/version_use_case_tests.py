import unittest
from unittest.mock import MagicMock

from sdk.common.utils import inject
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField
from sdk.versioning.router.versioning_requests import IncreaseVersionRequestObject
from sdk.versioning.use_case.versioning_use_case import IncreaseVersionUseCase


class IncreaseVersionUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._version = MagicMock()
        self._new_version = VersionField("1.2.3")

        def bind(binder):
            binder.bind(Version, self._version)

        inject.clear_and_configure(bind)

    @staticmethod
    def _execute_use_case(data: dict):
        req_obj = IncreaseVersionRequestObject.from_dict(data)
        use_case = IncreaseVersionUseCase()
        use_case.execute(req_obj)

    def test_success_update_server_version(self):
        self._version.server = VersionField("0.0.0")
        new_version = VersionField("1.2.3")
        self._execute_use_case(
            {IncreaseVersionRequestObject.SERVER_VERSION: new_version}
        )
        self.assertEqual(self._version.server, new_version)

    def test_success_update_api_version(self):
        self._version.api = "v1"
        new_version = "v2"
        self._execute_use_case({IncreaseVersionRequestObject.API_VERSION: new_version})
        self.assertEqual(self._version.api, new_version)


if __name__ == "__main__":
    unittest.main()
