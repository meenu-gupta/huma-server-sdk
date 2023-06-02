import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from extensions.deployment.router.deployment_requests import (
    UpdateLocalizationsRequestObject,
)
from extensions.deployment.use_case.update_localizations_use_case import (
    UpdateLocalizationsUseCase,
)
from extensions.tests.deployment.UnitTests.test_helpers import get_sample_localizations
from sdk.common.utils.convertible import ConvertibleClassValidationError


class MockRepo:
    update_localizations = MagicMock()


class UpdateLocalizationsTests(TestCase):
    KEY = UpdateLocalizationsRequestObject.LOCALIZATIONS

    def test_failure_update_localizations_request_object_with_invalid_lang(self):
        invalid_lang = "invalid lang"
        data = get_sample_localizations()
        data[self.KEY][invalid_lang] = {"hu_deployment_name": "name"}
        expected_message = f'Language "{invalid_lang}" is not supported.'
        with self.assertRaises(ConvertibleClassValidationError) as e:
            UpdateLocalizationsRequestObject.from_dict(data)
        self.assertIn(expected_message, e.exception.debug_message)

    def test_failure_update_localizations_request_object_with_wrong_format(self):
        req_obj = get_sample_localizations()
        req_obj[self.KEY]["en"]["hu_deployment_name"] = {"name": "name"}
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateLocalizationsRequestObject.from_dict(req_obj)

    def test_success_create_localizations(self):
        request_object = UpdateLocalizationsRequestObject.from_dict(
            get_sample_localizations()
        )
        UpdateLocalizationsUseCase(MockRepo()).execute(request_object)
        MockRepo.update_localizations.assert_called_once()


if __name__ == "__main__":
    unittest.main()
