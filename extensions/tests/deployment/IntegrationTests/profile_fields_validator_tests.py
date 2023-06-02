from datetime import datetime

from bson import ObjectId
from dateutil.relativedelta import relativedelta

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment, Profile, ProfileFields
from sdk.common.utils.validators import utc_date_to_str
from .abstract_deployment_test_case_tests import AbstractDeploymentTestCase

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"


class ProfileFieldsValidatorsTestCase(AbstractDeploymentTestCase):
    override_config = {"server.deployment.userProfileValidation": "true"}

    def setUp(self):
        super(ProfileFieldsValidatorsTestCase, self).setUp()
        self.user_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}"
        self.headers = self.get_headers_for_token(VALID_USER_ID)
        self.remove_onboarding()

    def test_success_update_date_of_birth__in_max_range(self):
        """deployment is configured to allow only 18 years old people"""
        years_ago_18 = datetime.utcnow() - relativedelta(years=18)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_18.date())}
        rsp = self.flask_client.post(self.user_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code, rsp.json)

    def test_success_update_date_of_birth__in_min_range(self):
        """deployment is configured to allow only users under 100 y.o"""
        years_ago_94 = datetime.utcnow() - relativedelta(years=94)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_94.date())}
        rsp = self.flask_client.post(self.user_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code, rsp.json)

    def test_failure_update_date_of_birth__out_of_max_range(self):
        """deployment is configured to allow only users over 18 y.o."""
        years_ago_18 = datetime.utcnow() - relativedelta(years=5)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_18.date())}
        self.assertUpdateFailed(body)

    def test_failure_update_date_of_birth__out_of_min_range(self):
        """deployment is configured to allow only users under 100 y.o"""
        years_ago_101 = datetime.utcnow() - relativedelta(years=101)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_101.date())}
        self.assertUpdateFailed(body)

    def test_success_update_date_of_birth_no_time_comparison(self):
        years_ago_100 = datetime.utcnow() - relativedelta(years=100)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_100.date())}
        rsp = self.flask_client.post(self.user_route, json=body, headers=self.headers)

        self.assertEqual(200, rsp.status_code, rsp.json)

    def test_success_update_date_of_birth_not_in_un_editable_fields(self):
        years_ago_18 = datetime.utcnow() - relativedelta(years=18)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_18)}
        rsp = self.flask_client.post(self.user_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code, rsp.json)

    def test_failure_update_date_of_birth_in_un_editable_fields(self):
        years_ago_18 = datetime.utcnow() - relativedelta(years=18)
        self.set_un_editable_field(User.DATE_OF_BIRTH)
        body = {User.DATE_OF_BIRTH: utc_date_to_str(years_ago_18)}
        rsp = self.flask_client.post(self.user_route, json=body, headers=self.headers)
        self.assertEqual(200, rsp.status_code, rsp.json)

        body = {
            User.DATE_OF_BIRTH: utc_date_to_str(years_ago_18 + relativedelta(days=1))
        }
        self.assertUpdateFailed(body)

    def set_un_editable_field(self, field):
        self.mongo_database.deployment.update_one(
            {"_id": ObjectId("5d386cc6ff885918d96edb2c")},
            {
                "$set": {
                    f"{Deployment.PROFILE}.{Profile.FIELDS}.{ProfileFields.UN_EDITABLE_FIELDS}": [
                        field
                    ]
                }
            },
        )

    def assertUpdateFailed(self, body):
        rsp = self.flask_client.post(self.user_route, json=body, headers=self.headers)
        self.assertEqual(403, rsp.status_code)
        self.assertIn(User.DATE_OF_BIRTH, rsp.json["message"])
