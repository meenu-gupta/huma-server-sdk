from bson import ObjectId

from extensions.tests.deployment.IntegrationTests.abstract_deployment_test_case_tests import (
    AbstractDeploymentTestCase,
)

VALID_USER_ID = "5e8f0c74b50aa9656c34789c"
VALID_ADMIN_ID = "5e8f0c74b50aa9656c34789b"


def extra_custom_fields_configs():
    return {
        "insuranceNumber": {
            "errorMessage": "Insurance Number is incorrect",
            "validation": "\\d{7}",
            "onboardingCollectionText": "Please enter mediclinic number",
            "profileCollectionText": "Patient Unique ID",
            "required": True,
            "clinicianUpdate": True,
            "showClinicianHeader": True,
            "type": "TEXT",
            "order": 2,
            "isPrimary": False,
        }
    }


class ExtraCustomIdsTestCase(AbstractDeploymentTestCase):
    override_config = {
        **AbstractDeploymentTestCase.override_config,
        "server.deployment.userProfileValidation": "true",
    }
    user_route = f"/api/extensions/v1beta/user/{VALID_USER_ID}"

    def setUp(self):
        super(ExtraCustomIdsTestCase, self).setUp()
        self.remove_onboarding()

    def remove_onboarding(self):
        self.mongo_database["deployment"].update_one(
            {"_id": ObjectId("5d386cc6ff885918d96edb2c")},
            {"$unset": {"onboardingConfigs": 1}},
        )

    def update_profile_and_assert_code_equal(self, body: dict, code: int):
        rsp = self.flask_client.post(
            self.user_route,
            json=body,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(code, rsp.status_code)

    def test_success_update_profile_with_correct_mediclinic_number(self):
        body = {"extraCustomFields": {"mediclinicNumber": "0123456"}}
        self.update_profile_and_assert_code_equal(body, 200)

        rsp = self.flask_client.get(
            self.user_route,
            headers=self.get_headers_for_token(VALID_USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        user_dict = rsp.json
        self.assertIn("extraCustomFields", user_dict)
        self.assertIn("mediclinicNumber", user_dict["extraCustomFields"])

    def test_success_update_profile_no_mediclinic_number(self):
        body = {"timezone": "Europe/London"}
        self.update_profile_and_assert_code_equal(body, 200)

    def test_failure_update_profile_with_correct_mediclinic_number(self):
        body = {"extraCustomFields": {"mediclinicNumber": "012345"}}
        self.update_profile_and_assert_code_equal(body, 403)

    def test_failure_update_profile_with_field_not_in_deployment_extra_fields(self):
        body = {"extraCustomFields": {"wrongFieldName": "0123450"}}
        self.update_profile_and_assert_code_equal(body, 403)

    def test_success_create_extra_custom_field(self):
        deployment_url = f"/api/extensions/v1beta/deployment/{self.deployment_id}"
        admin_headers = self.get_headers_for_token(VALID_ADMIN_ID)
        configs = extra_custom_fields_configs()
        body = {"extraCustomFields": configs}
        rsp = self.flask_client.put(
            deployment_url,
            json=body,
            headers=admin_headers,
        )
        self.assertEqual(200, rsp.status_code)
        rsp = self.flask_client.get(deployment_url, headers=admin_headers)
        self.assertEqual(200, rsp.status_code)
        deployment = rsp.json
        self.assertDictEqual(configs, deployment["extraCustomFields"])

    def test_failure_create_extra_custom_field_two_primary_fields(self):
        deployment_url = f"/api/extensions/v1beta/deployment/{self.deployment_id}"
        admin_headers = self.get_headers_for_token(VALID_ADMIN_ID)
        configs = extra_custom_fields_configs()
        configs["mediclinicNumber"] = configs["insuranceNumber"]
        configs["mediclinicNumber"]["isPrimary"] = True
        configs["insuranceNumber"]["isPrimary"] = True
        body = {"extraCustomFields": configs}
        rsp = self.flask_client.put(
            deployment_url,
            json=body,
            headers=admin_headers,
        )
        self.assertEqual(403, rsp.status_code)
