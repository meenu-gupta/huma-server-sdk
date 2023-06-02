import unittest

from extensions.deployment.models.deployment import Features, AppMenuItem
from sdk.common.utils.convertible import ConvertibleClassValidationError


class AppMenuTestCase(unittest.TestCase):
    def test_default_app_menu(self):
        features = Features()
        self.assertEqual(features.appMenu, AppMenuItem.default_app_view())

    def test_failure_create_app_menu_empty(self):
        data = {"appMenu": []}
        with self.assertRaises(ConvertibleClassValidationError):
            Features.from_dict(data)

    def test_failure_create_app_menu_too_many_items(self):
        data = {
            "appMenu": [
                AppMenuItem.CARE_PLAN.value,
                AppMenuItem.KEY_ACTIONS.value,
                AppMenuItem.TO_DO.value,
                AppMenuItem.TRACK.value,
                AppMenuItem.LEARN.value,
                AppMenuItem.PROFILE.value,
            ]
        }
        with self.assertRaises(ConvertibleClassValidationError):
            Features.from_dict(data)

    def test_success_create_app_menu(self):
        data = {
            "appMenu": [
                AppMenuItem.TO_DO.value,
                AppMenuItem.TRACK.value,
                AppMenuItem.LEARN.value,
                AppMenuItem.PROFILE.value,
            ]
        }
        expected_result = [
            AppMenuItem.TO_DO,
            AppMenuItem.TRACK,
            AppMenuItem.LEARN,
            AppMenuItem.PROFILE,
        ]
        features = Features.from_dict(data)
        self.assertEqual(expected_result, features.appMenu)
