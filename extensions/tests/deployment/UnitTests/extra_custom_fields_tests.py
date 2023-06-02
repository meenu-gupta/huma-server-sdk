from unittest import TestCase

from extensions.authorization.models.user import User
from extensions.deployment.callbacks import validate_extra_custom_fields
from extensions.deployment.models.deployment import ExtraCustomFieldConfig, Deployment
from sdk.common.utils.convertible import ConvertibleClassValidationError
from dataclasses import fields


def extra_custom_fields_configs():
    return {
        "mediclinicNumber": {
            "errorMessage": "Insurance Number is incorrect",
            "description": "Please enter mediclinic number description",
            "validation": "\\d{7}",
            "onboardingCollectionText": "Please enter mediclinic number",
            "profileCollectionText": "Patient Unique ID",
            "required": True,
            "clinicianUpdate": True,
            "showClinicianHeader": True,
            "type": "TEXT",
            "order": 2,
            "isPrimary": True,
        }
    }


class ExtraCustomFieldsTestCase(TestCase):
    extra_custom_fields = {
        key: ExtraCustomFieldConfig.from_dict(value)
        for key, value in extra_custom_fields_configs().items()
    }

    def test_success_validate_extra_field(self):
        user = User.from_dict(
            {User.EXTRA_CUSTOM_FIELDS: {"mediclinicNumber": "0123456"}}
        )
        validate_extra_custom_fields(user, self.extra_custom_fields)

    def test_failure_validate_extra_field_missing_config(self):
        user = User.from_dict({User.EXTRA_CUSTOM_FIELDS: {"mediclinicId": "0123456"}})
        with self.assertRaises(ConvertibleClassValidationError):
            validate_extra_custom_fields(user, self.extra_custom_fields)

    def test_failure_validate_extra_field_wrong_format(self):
        user = User.from_dict(
            {User.EXTRA_CUSTOM_FIELDS: {"mediclinicNumber": "012345"}}
        )
        with self.assertRaises(ConvertibleClassValidationError):
            validate_extra_custom_fields(user, self.extra_custom_fields)

    def test_success_convert_with_none(self):
        required_fields = [
            field.name
            for field in fields(ExtraCustomFieldConfig)
            if not field.metadata.get("required")
        ]
        for field_name in required_fields:
            custom_field = extra_custom_fields_configs()["mediclinicNumber"]
            custom_field[field_name] = None
            try:
                ExtraCustomFieldConfig.from_dict(custom_field)
            except ConvertibleClassValidationError as error:
                self.fail(error)

    def test_failure_with_length(self):
        request_dict = {
            x: extra_custom_fields_configs()["mediclinicNumber"]
            for x in [1, 2, 3, 4, 5, 6]
        }
        with self.assertRaises(ConvertibleClassValidationError):
            Deployment.from_dict({Deployment.EXTRA_CUSTOM_FIELDS: request_dict})
