from unittest import TestCase
from unittest.mock import MagicMock

from bson import ObjectId

from extensions.authorization.models.user import User
from extensions.authorization.models.user_fields_converter import UserFieldsConverter
from extensions.deployment.models.deployment import Deployment
from extensions.tests.authorization.IntegrationTests.test_helpers import DEPLOYMENT_CODE
from extensions.tests.export_deployment.UnitTests.export_unit_tests import ENROLLMENT_ID
from sdk.common.localization.utils import Localization
from sdk.common.utils import inject

USER_ID = "5ff59bcccb7dcaa4d6a6b8d8"
DEPLOYMENT_ID = "5ff59bcccb7dcaa4d6a6b8d9"


class TestUserFieldConverter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind_and_configure(binder):
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    @staticmethod
    def get_user(user_id):
        return User(id=user_id, roles=[])

    def test_display_all_available_data(self):
        converter = UserFieldsConverter(self.get_user("5ff59bcccb7dcaa4d6a6b8d8"))
        data = converter.to_dict()
        fields_to_be_present = [
            User.ID,
            User.ROLES,
        ]
        self.assertEqual(len(data.keys()), len(fields_to_be_present))
        for field in data.keys():
            self.assertIn(field, fields_to_be_present)

    def test_display_only_fields(self):
        converter = UserFieldsConverter(self.get_user("5ff59bcccb7dcaa4d6a6b8d8"))
        data = converter.to_dict(only_fields={User.ID})
        self.assertEqual(len(data.keys()), 1)

    def test_enrollment_number_not_added_no_needed_data(self):
        user = User(id=ObjectId())
        deployment = Deployment(id=ObjectId())
        converter = UserFieldsConverter(user, deployment)
        data = converter.to_dict()
        enrollment_number = data.get(User.ENROLLMENT_NUMBER)
        self.assertIsNone(enrollment_number)

    def test_enrollment_number_not_added_no_user_data(self):
        user = User(id=ObjectId())
        deployment = Deployment(id=ObjectId(), code=DEPLOYMENT_CODE)
        converter = UserFieldsConverter(user, deployment)
        user_dict = converter.to_dict()
        enrollment_number = user_dict.get(User.ENROLLMENT_NUMBER)
        self.assertIsNone(enrollment_number)

    def test_enrollment_number_not_added_no_deployment_data(self):
        user = User(id=ObjectId(), enrollmentId=ENROLLMENT_ID)
        deployment = Deployment(id=ObjectId())
        converter = UserFieldsConverter(user, deployment)
        user_dict = converter.to_dict()
        enrollment_number = user_dict.get(User.ENROLLMENT_NUMBER)
        self.assertIsNone(enrollment_number)

    def test_enrollment_number_added_properly(self):
        user = User(id=ObjectId(), enrollmentId=ENROLLMENT_ID)
        deployment = Deployment(id=ObjectId(), code=DEPLOYMENT_CODE)
        converter = UserFieldsConverter(user, deployment)
        user_dict = converter.to_dict()
        enrollment_number = user_dict.get(User.ENROLLMENT_NUMBER)
        self.assertIsNotNone(enrollment_number)
        self.assertEqual("AU15-0100", enrollment_number)
