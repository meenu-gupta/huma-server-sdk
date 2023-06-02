import json
import shutil
from pathlib import Path
from unittest.mock import patch

from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
    ExportUsersRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
)
from extensions.export_deployment.use_case.exportable.consent_exportable_use_case import (
    ConsentExportableUseCase,
)
from extensions.module_result.models.primitives import Symptom, ComplexSymptomValue
from extensions.module_result.modules import NorfolkQuestionnaireModule
from extensions.tests.export_deployment.IntegrationTests.export_deployment_router_tests import (
    ExportTestCase,
    LAYER,
    QUANTITY,
    VIEW,
    BINARY,
    NESTED_LAYER,
    SINGLE_QTY,
    DAY_VIEW,
    MODULE_VIEW,
    BINARY_INCLUDE,
    download_file_mock,
    MODULE_NAMES,
    FORMAT,
    JSON_CSV_FORMAT,
    ONBOARDING_MODULE_NAMES,
    USER_IDS,
    FROM_DATE,
    SINGLE_VIEW,
    FLAT_LAYER,
    MULTIPLE_QTY,
    JSON_FORMAT,
)
from extensions.tests.export_deployment.IntegrationTests.export_permission_tests import (
    ORGANIZATION_DEPLOYMENT_ID,
    ORG_DEPLOYMENT_USER,
)
from sdk.common.adapter.minio.minio_file_storage_adapter import MinioFileStorageAdapter

QUESTIONNAIRE_DEPLOYMENT_ID = "614b51bce422623dcb0e455c"
ADMIN_USER_ID = "5e8f0c74b50aa9656c34789b"
MEDICATIONS_DEPLOYMENT_ID = "1d386cc6ff885918d96edb2f"


class SingleDeploymentExportTestCase(ExportTestCase):
    def setUp(self):
        super(SingleDeploymentExportTestCase, self).setUp()
        self.data = self.get_sample_request_data(
            deployment_id=ORGANIZATION_DEPLOYMENT_ID
        )

    def test_export_single_flat_view_including_fields__keeps_default_included_fields(
        self,
    ):
        self.data[VIEW] = SINGLE_VIEW
        self.data[LAYER] = FLAT_LAYER
        self.data[QUANTITY] = MULTIPLE_QTY
        self.data[FORMAT] = JSON_FORMAT
        self.data[ExportRequestObject.DEIDENTIFIED] = True
        self.data[ExportRequestObject.QUESTIONNAIRE_PER_NAME] = True
        self.data[ExportRequestObject.INCLUDE_USER_META_DATA] = True
        self.data[ExportRequestObject.SINGLE_FILE_RESPONSE] = True
        self.data[ExportRequestObject.TRANSLATE_PRIMITIVES] = False
        self.data[ExportRequestObject.USE_FLAT_STRUCTURE] = True
        self.data[ExportRequestObject.INCLUDE_FIELDS] = [
            "user",
        ]
        resp = self.request_export(self.data, ADMIN_USER_ID)
        self.assert_jsons_are_equal(
            resp,
            "single_flat_view_keeps_default_included_fields.json",
        )

    def test_export_medications_data__deidentified_view_successful(self):
        data = self.get_sample_request_data(deployment_id=MEDICATIONS_DEPLOYMENT_ID)
        data[FORMAT] = JSON_CSV_FORMAT
        data[ExportRequestObject.DEIDENTIFIED] = True
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(resp, "medications_deidentified.zip")

    def test_export_medications_data__identifiable_view_successful(self):
        data = self.get_sample_request_data(deployment_id=MEDICATIONS_DEPLOYMENT_ID)
        data[FORMAT] = JSON_CSV_FORMAT
        data[ExportRequestObject.DEIDENTIFIED] = False
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(resp, "medications.zip")

    def test_export_nested_user_view_multiple_quantity_with_consent(self):
        data = self.get_sample_request_data(deployment_id=QUESTIONNAIRE_DEPLOYMENT_ID)
        data[LAYER] = NESTED_LAYER
        data[ONBOARDING_MODULE_NAMES] = [ConsentExportableUseCase.onboardingModuleName]
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_user_view_multiple_with_consent.zip"
        )

    def test_export_nested_day_view_multiple_quantity_with_consent(self):
        data = self.get_sample_request_data(deployment_id=QUESTIONNAIRE_DEPLOYMENT_ID)
        data[LAYER] = NESTED_LAYER
        data[VIEW] = DAY_VIEW
        data[ONBOARDING_MODULE_NAMES] = [ConsentExportableUseCase.onboardingModuleName]
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_day_view_multiple_with_consent.zip"
        )

    def test_export_nested_module_view_multiple_quantity_with_consent(self):
        data = self.get_sample_request_data(deployment_id=QUESTIONNAIRE_DEPLOYMENT_ID)
        data[LAYER] = NESTED_LAYER
        data[VIEW] = MODULE_VIEW
        data[ONBOARDING_MODULE_NAMES] = [ConsentExportableUseCase.onboardingModuleName]
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_module_view_multiple_with_consent.zip"
        )

    def test_export_nested_module_view_multiple_quantity_with_consent_filtered_by_date(
        self,
    ):
        data = self.get_sample_request_data(deployment_id=QUESTIONNAIRE_DEPLOYMENT_ID)
        data[LAYER] = NESTED_LAYER
        data[VIEW] = MODULE_VIEW
        data[ONBOARDING_MODULE_NAMES] = [ConsentExportableUseCase.onboardingModuleName]
        data[FROM_DATE] = "2021-09-23T10:30:00Z"
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(
            resp,
            "single_deployment_nested_module_view_multiple_with_consent_by_date.zip",
        )

    def test_export_nested_module_view_multiple_quantity_with_consent_filtered_by_user(
        self,
    ):
        data = self.get_sample_request_data(deployment_id=QUESTIONNAIRE_DEPLOYMENT_ID)
        data[LAYER] = NESTED_LAYER
        data[VIEW] = MODULE_VIEW
        data[ONBOARDING_MODULE_NAMES] = [ConsentExportableUseCase.onboardingModuleName]
        data[USER_IDS] = [ORG_DEPLOYMENT_USER]
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(
            resp,
            "single_deployment_nested_module_view_multiple_with_consent_by_user.zip",
        )

    def test_export_nested_user_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_user_view_multiple.zip"
        )

    def test_export_nested_user_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_user_view_single.zip"
        )

    def test_export_nested_day_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = DAY_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_day_view_multiple.zip"
        )

    def test_export_nested_day_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "single_deployment_nested_day_view_single.zip")

    def test_export_nested_module_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_module_view_multiple.zip"
        )

    def test_export_nested_module_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_module_view_single.zip"
        )

    def test_export_flat_user_view_multiple_quantity(self):
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_flat_user_view_multiple.zip"
        )

    def test_export_flat_user_view_single_quantity(self):
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "single_deployment_flat_user_view_single.zip")

    def test_export_flat_day_view_multiple_quantity(self):
        self.data[VIEW] = DAY_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "single_deployment_flat_day_view.zip")

    def test_export_flat_day_view_single_quantity(self):
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "single_deployment_flat_day_view_single.zip")

    def test_export_flat_module_view_multiple_quantity(self):
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_flat_module_view_multiple.zip"
        )

    def test_export_flat_module_view_single_quantity(self):
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_flat_module_view_single.zip"
        )

    def test_export_multiple_primitive_questionnaire_module(self):
        data = self.get_sample_request_data(deployment_id=QUESTIONNAIRE_DEPLOYMENT_ID)
        data[MODULE_NAMES] = [NorfolkQuestionnaireModule.moduleId]
        data[FORMAT] = JSON_CSV_FORMAT
        resp = self.request_export(data, ADMIN_USER_ID)
        self.assert_zips_are_equal(
            resp, "single_deployment_multiple_primitive_questionnaire.zip"
        )


class DeIdentifiedSingleDeploymentExportTestCase(ExportTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.get_sample_request_data(
            deployment_id=ORGANIZATION_DEPLOYMENT_ID, deidentified=True
        )

    def test_export_flat_module_view_deidentified(self):
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_flat_module_view_deidentified.zip"
        )

    def test_export_nested_module_view_deidentified(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_nested_module_deidentified.zip"
        )

    def test_export_flat_user_view_single_deidentified(self):
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "single_deployment_flat_user_view_single_deidentified.zip"
        )

    def test_export_nested_user_view_multiple_deidentified_with_binaries(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[BINARY] = BINARY_INCLUDE
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            download_file_mock,
        ):
            resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp,
            "single_deployment_nested_user_view_multiple_deidentified_with_binaries.zip",
        )

    def test_export_flat_user_view_multiple_deidentified_with_binaries(self):
        self.data[BINARY] = BINARY_INCLUDE
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            download_file_mock,
        ):
            resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp,
            "single_deployment_flat_user_view_multiple_deidentified_with_binaries.zip",
        )


class ExportUserTests(ExportTestCase):
    fixtures = [
        Path(__file__).parent.joinpath("fixtures/deployment_dump.json"),
    ]
    DEPLOYMENT_ID = "60d9b623b07e15e833eae4a5"
    VALID_USER_ID = "60e1fe8a3d632b2d0e3694d8"
    VALID_MANAGER_ID = "60df12c29e8a91c79ea079f8"
    ARABIC_ANSWER = "arabic answer aval"

    def setUp(self):
        super().setUp()
        self.headers = self.get_headers_for_token(self.VALID_MANAGER_ID)
        self.base_route = "/api/extensions/v1beta/export"

    def export_symptom_json_result(self, body):
        request_object = ExportUsersRequestObject.from_dict(body)
        use_case = ExportDeploymentUseCase()
        response_object = use_case.execute(request_object)
        archive_path = response_object.value.filename
        shutil.unpack_archive(archive_path, Path(archive_path).parent)
        user_export_data_path = Path(archive_path).parent.joinpath(self.VALID_USER_ID)

        with open(user_export_data_path.joinpath("Symptom.json"), "rb") as sample_file:
            module_export_result = json.load(sample_file)
        return module_export_result

    def test_success_export_data(self):
        path = f"{self.base_route}/"
        body = {ExportRequestObject.DEPLOYMENT_ID: self.DEPLOYMENT_ID}
        rsp = self.flask_client.post(path, headers=self.headers, json=body)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual("application/zip", rsp.mimetype)

    def test_export_method_call_with_translation(self):
        body = {ExportRequestObject.DEPLOYMENT_ID: self.DEPLOYMENT_ID}
        module_export_result = self.export_symptom_json_result(body)
        self.assertEqual(
            module_export_result[0][Symptom.COMPLEX_VALUES][0][
                ComplexSymptomValue.NAME
            ],
            self.ARABIC_ANSWER,
        )

    def test_export_method_call_without_translation(self):
        body = {
            ExportRequestObject.DEPLOYMENT_ID: self.DEPLOYMENT_ID,
            ExportRequestObject.DO_TRANSLATE: False,
        }
        module_export_result = self.export_symptom_json_result(body)
        self.assertNotEqual(
            module_export_result[0][Symptom.COMPLEX_VALUES][0][
                ComplexSymptomValue.NAME
            ],
            self.ARABIC_ANSWER,
        )
