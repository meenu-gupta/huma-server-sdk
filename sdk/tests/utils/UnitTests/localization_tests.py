import unittest

from sdk.common.localization.utils import Language, validate_localizations

LANGUAGES_TO_BE_IN_SYSTEM = [
    "en-GB",
    "de-DE",
    "en",
    "en-US",
    "de",
    "fr",
    "es",
    "sv",
    "ca",
    "ar",
    "nl",
    "it",
    "de-AT",
    "de-CH",
]


class LocalizationTestCase(unittest.TestCase):
    def test_success_get_valid_languages(self):
        languages = Language.get_valid_languages()
        self.assertTrue(all(item in LANGUAGES_TO_BE_IN_SYSTEM for item in languages))

    def test_success_validate_localizations(self):
        localizations = {key: {} for key in LANGUAGES_TO_BE_IN_SYSTEM}
        self.assertTrue(validate_localizations(localizations))

    def test_failure_validate_localizations_non_existing(self):
        with self.assertRaises(KeyError):
            validate_localizations({"ru": {}})


if __name__ == "__main__":
    unittest.main()
