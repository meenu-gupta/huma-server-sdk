from unittest.mock import patch

from extensions.export_deployment.exceptions import ExportErrorCodes
from extensions.export_deployment.models.export_deployment_models import (
    ExportProfile,
    ExportParameters,
)
from extensions.export_deployment.models.mongo_export_deployment_models import (
    MongoExportProfile,
)
from extensions.export_deployment.use_case.exportable.consent_exportable_use_case import (
    ConsentExportableUseCase,
)
from extensions.tests.export_deployment.IntegrationTests.export_deployment_router_tests import (
    ExportTestCase,
    LAYER,
    NESTED_LAYER,
    JSON_CSV_FORMAT,
)

NEW_DEFAULT_PROFILE = "new default"
DEFAULT_PROFILE = "current default"
NOT_DEFAULT_PROFILE = "not default"
NOT_DEFAULT_PROFILE_ID = "6094f6fe39396aeae7696246"
DEPLOYMENT_ID = "5d386cc6ff885918d96edb2f"
ORGANIZATION_ID = "5d386cc6ff885918d96eda1b"
DEFAULT_PROFILE_FOR_DEPLOYMENT = "default for deployment"

USE_CASES_PATH = "extensions.export_deployment.use_case.export_use_cases"


class ProfileExportTestCase(ExportTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.get_sample_request_data(deployment_ids=[DEPLOYMENT_ID])
        self.data[LAYER] = NESTED_LAYER

    def retrieve_profile(self, profile_name: str = None) -> ExportProfile:
        export_profile = MongoExportProfile.objects(name=profile_name).first()
        return ExportProfile.from_dict(export_profile.to_dict())

    def test_create_default_profile_updates_old_default(self):
        profile_request_params = {ExportParameters.FROM_DATE: "2020-09-11"}
        profile_data = {
            ExportProfile.NAME: NEW_DEFAULT_PROFILE,
            ExportProfile.ORGANIZATION_ID: ORGANIZATION_ID,
            ExportProfile.CONTENT: profile_request_params,
            ExportProfile.DEFAULT: True,
        }

        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(201, resp.status_code)

        new_profile = self.retrieve_profile(NEW_DEFAULT_PROFILE)
        self.assertTrue(new_profile.default)
        self.assertEqual(NEW_DEFAULT_PROFILE, new_profile.name)

        old_profile = self.retrieve_profile(DEFAULT_PROFILE)
        self.assertFalse(old_profile.default)
        self.assertEqual(DEFAULT_PROFILE, old_profile.name)

    def test_update_to_default_profile_updates_old_default(self):
        profile_request_params = {ExportParameters.FROM_DATE: "2020-09-11"}
        profile_data = {
            ExportProfile.NAME: NOT_DEFAULT_PROFILE,
            ExportProfile.DEPLOYMENT_ID: DEPLOYMENT_ID,
            ExportProfile.CONTENT: profile_request_params,
            ExportProfile.DEFAULT: True,
        }
        url = "/api/extensions/v1beta/export/profile/6094f6fe39396aeae7696247"
        resp = self.flask_client.post(url, json=profile_data)
        self.assertEqual(200, resp.status_code)

        updated_profile = self.retrieve_profile(NOT_DEFAULT_PROFILE)
        self.assertTrue(updated_profile.default)
        self.assertEqual(NOT_DEFAULT_PROFILE, updated_profile.name)

        old_profile = self.retrieve_profile(DEFAULT_PROFILE_FOR_DEPLOYMENT)
        self.assertFalse(old_profile.default)
        self.assertEqual(DEFAULT_PROFILE_FOR_DEPLOYMENT, old_profile.name)

    def test_unique_profile_for_deployment(self):
        profile_data = {
            ExportProfile.NAME: NOT_DEFAULT_PROFILE,
            ExportProfile.DEPLOYMENT_ID: DEPLOYMENT_ID,
            ExportProfile.CONTENT: {},
            ExportProfile.DEFAULT: True,
        }
        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual(ExportErrorCodes.DUPLICATE_PROFILE_NAME, resp.json["code"])

    def test_unique_profile_for_organization(self):
        profile_data = {
            ExportProfile.NAME: DEFAULT_PROFILE,
            ExportProfile.ORGANIZATION_ID: ORGANIZATION_ID,
            ExportProfile.CONTENT: {},
            ExportProfile.DEFAULT: True,
        }
        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual(ExportErrorCodes.DUPLICATE_PROFILE_NAME, resp.json["code"])

    def test_unique_profile_for_organization_does_not_affect_deployment(self):
        profile_data = {
            ExportProfile.NAME: DEFAULT_PROFILE,
            ExportProfile.DEPLOYMENT_ID: DEPLOYMENT_ID,
            ExportProfile.CONTENT: {},
            ExportProfile.DEFAULT: True,
        }
        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(201, resp.status_code)

    @patch(f"{USE_CASES_PATH}.ExportDeploymentUseCase.process_request")
    def test_default_fields_not_updates_profile_when_not_passed(
        self, mocked_process_request
    ):
        profile_request_params = {
            ExportParameters.FORMAT: JSON_CSV_FORMAT,
        }
        profile_data = {
            ExportProfile.NAME: NEW_DEFAULT_PROFILE,
            ExportProfile.ORGANIZATION_ID: ORGANIZATION_ID,
            ExportProfile.CONTENT: profile_request_params,
            ExportProfile.DEFAULT: True,
        }
        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(201, resp.status_code)

        request_data = {ExportParameters.ORGANIZATION_ID: ORGANIZATION_ID}
        self.flask_client.post("/api/extensions/v1beta/export/", json=request_data)

        called_request_object = mocked_process_request.call_args.args[0]
        self.assertEqual(
            ExportParameters.DataFormatOption.JSON_CSV, called_request_object.format
        )

    @patch(f"{USE_CASES_PATH}.ExportDeploymentUseCase.process_request")
    def test_profile_onboarding_modules_used_during_export(
        self, mocked_process_request
    ):
        sample_modules = [ConsentExportableUseCase.onboardingModuleName]
        profile_content = {
            ExportParameters.ONBOARDING_MODULE_NAMES: sample_modules,
        }
        profile_data = {
            ExportProfile.NAME: NEW_DEFAULT_PROFILE,
            ExportProfile.ORGANIZATION_ID: ORGANIZATION_ID,
            ExportProfile.CONTENT: profile_content,
            ExportProfile.DEFAULT: True,
        }
        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(201, resp.status_code)

        request_data = {ExportParameters.ORGANIZATION_ID: ORGANIZATION_ID}
        self.flask_client.post("/api/extensions/v1beta/export/", json=request_data)

        called_request_object = mocked_process_request.call_args.args[0]
        self.assertEqual(sample_modules, called_request_object.onboardingModuleNames)

    def test_create_profile_with_empty_exclude_fields_valid(self):
        profile_request_params = {ExportParameters.EXCLUDE_FIELDS: []}
        profile_data = {
            ExportProfile.NAME: NEW_DEFAULT_PROFILE,
            ExportProfile.ORGANIZATION_ID: ORGANIZATION_ID,
            ExportProfile.CONTENT: profile_request_params,
            ExportProfile.DEFAULT: True,
        }
        resp = self.flask_client.post(
            "/api/extensions/v1beta/export/profile", json=profile_data
        )
        self.assertEqual(201, resp.status_code)
