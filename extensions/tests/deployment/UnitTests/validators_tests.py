from unittest import TestCase

from extensions.common.exceptions import (
    InvalidEthnicityOptionValueException,
    InvalidGenderOptionValueException,
)
from extensions.common.validators import (
    validate_ethnicity_options,
    validate_gender_options,
)
from extensions.deployment.models.deployment import EthnicityOption, GenderOptionType
from extensions.deployment.models.key_action_config import validate_duration_iso
from extensions.deployment.router.deployment_requests import extra_validate_duration_iso

INVALID_DURATION_ISO = "P0DTM0S"
VALID_DURATION_ISO = "P0DT5M60S"
NONE_INTERVAL_DURATION_ISO = "P0DT0M0S"


class GenderOptionValidatorTestCase(TestCase):
    def test_failure_gender_options(self):
        gender_options_data = [
            {"displayName": "Male", "value": "MALE"},
            {"displayName": "Female", "value": "Female"},
        ]
        gender_options = [
            GenderOptionType.from_dict(gender_option)
            for gender_option in gender_options_data
        ]
        with self.assertRaises(InvalidGenderOptionValueException):
            validate_gender_options(gender_options)

    def test_success_gender_options(self):
        gender_options_data = [
            {"displayName": "Male", "value": "MALE"},
            {"displayName": "Female", "value": "FEMALE"},
        ]
        gender_options = [
            GenderOptionType.from_dict(gender_option)
            for gender_option in gender_options_data
        ]
        validate_gender_options(gender_options)


class EthnicityOptionValidatorTestCase(TestCase):
    def test_failure_ethnicity_options(self):
        ethnicity_options_data = [
            {EthnicityOption.DISPLAY_NAME: "White", EthnicityOption.VALUE: "WHITE"},
            {
                EthnicityOption.DISPLAY_NAME: "Other Ethnic Groups",
                EthnicityOption.VALUE: "other_ethnic_groups",
            },
        ]
        ethnicity_options = [
            EthnicityOption.from_dict(ethnicity_option)
            for ethnicity_option in ethnicity_options_data
        ]
        with self.assertRaises(InvalidEthnicityOptionValueException):
            validate_ethnicity_options(ethnicity_options)

    def test_success_ethnicty_options(self):
        ethnicity_options_data = [
            {EthnicityOption.DISPLAY_NAME: "White", EthnicityOption.VALUE: "WHITE"},
            {
                EthnicityOption.DISPLAY_NAME: "Other Ethnic Groups",
                EthnicityOption.VALUE: "OTHER_ETHNIC_GROUPS",
            },
        ]
        ethnicity_options = [
            EthnicityOption.from_dict(ethnicity_option)
            for ethnicity_option in ethnicity_options_data
        ]
        validate_ethnicity_options(ethnicity_options)


class DurationValidationTestCase(TestCase):
    def test_success_validate_duration_iso(self):
        try:
            validate_duration_iso(VALID_DURATION_ISO)
        except Exception:
            self.fail()

    def test_failure_validate_duration_iso(self):
        with self.assertRaises(Exception):
            validate_duration_iso(INVALID_DURATION_ISO)

    def test_sucess_validate_non_0_interval(self):
        try:
            extra_validate_duration_iso(VALID_DURATION_ISO)
        except Exception:
            self.fail()

    def test_failure_validate_non_0_interval(self):
        with self.assertRaises(Exception):
            extra_validate_duration_iso(NONE_INTERVAL_DURATION_ISO)
