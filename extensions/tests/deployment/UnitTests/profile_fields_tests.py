from datetime import datetime
from unittest import TestCase

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import ProfileFields, FieldValidator
from sdk.common.utils.convertible import ConvertibleClassValidationError


class ProfileFieldsTestCase(TestCase):
    def test_success_duration_validation(self):
        data = {
            ProfileFields.VALIDATORS: {
                User.DATE_OF_BIRTH: {
                    FieldValidator.MIN_ISO_DURATION: "P1D",
                    FieldValidator.MAX_ISO_DURATION: "P1Y",
                }
            }
        }
        fields: ProfileFields = ProfileFields.from_dict(data)
        self.assertIsInstance(fields.validators[User.DATE_OF_BIRTH], FieldValidator)

    def test_failure_duration_validation(self):
        data = {
            ProfileFields.VALIDATORS: {
                User.DATE_OF_BIRTH: {
                    FieldValidator.MIN_ISO_DURATION: "test",
                    FieldValidator.MAX_ISO_DURATION: "test",
                }
            }
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ProfileFields.from_dict(data)

    def test_success_date_validation(self):
        data = {
            ProfileFields.VALIDATORS: {
                User.DATE_OF_BIRTH: {FieldValidator.MIN: "2021-10-10T10:00:00.000Z"}
            }
        }
        fields: ProfileFields = ProfileFields.from_dict(data)
        self.assertIsInstance(fields.validators[User.DATE_OF_BIRTH].min, datetime)

    def test_failure_date_validation(self):
        data = {
            ProfileFields.VALIDATORS: {
                User.DATE_OF_BIRTH: {FieldValidator.MIN: "wrong_date"}
            }
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ProfileFields.from_dict(data)
