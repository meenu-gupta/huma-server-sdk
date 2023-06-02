from unittest.mock import patch

from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.tests.export_deployment.IntegrationTests.export_deployment_router_tests import (
    ExportTestCase,
    LAYER,
    QUANTITY,
    VIEW,
    BINARY,
    NESTED_LAYER,
    FLAT_LAYER,
    SINGLE_QTY,
    MULTIPLE_QTY,
    DAY_VIEW,
    USER_VIEW,
    MODULE_VIEW,
    BINARY_INCLUDE,
    download_file_mock,
    FORMAT,
    JSON_CSV_FORMAT,
    CSV_FORMAT,
    PREFER_SHORT_CODE,
)
from extensions.tests.export_deployment.IntegrationTests.export_permission_tests import (
    ORGANIZATION_DEPLOYMENT_ID,
    VALID_ORGANIZATION_ID,
)
from sdk.common.adapter.minio.minio_file_storage_adapter import MinioFileStorageAdapter

ORGANIZATION_DEPLOYMENT_ID_2 = "5d386cc6ff885918d96edb2a"
AZ_QUESTIONNAIRE_DEPLOYMENT = "5d386cc6ff885918d96edb9c"


class MultiDeploymentExportTestCase(ExportTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.get_sample_request_data(
            deployment_ids=[ORGANIZATION_DEPLOYMENT_ID_2, ORGANIZATION_DEPLOYMENT_ID]
        )


class MultipleFilesExportTestCase(MultiDeploymentExportTestCase):
    def test_export_nested_user_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_user_view_multiple.zip"
        )

    def test_export_nested_user_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_user_view_single.zip"
        )

    def test_export_nested_day_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = DAY_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_day_view_multiple.zip"
        )

    def test_export_nested_day_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_day_view_single.zip"
        )

    def test_export_nested_module_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_module_view_multiple.zip"
        )

    def test_export_nested_module_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_module_view_single.zip"
        )

    def test_export_flat_user_view_multiple_quantity(self):
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_user_view_multiple.zip"
        )

    def test_export_flat_user_view_single_quantity(self):
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_user_view_single.zip"
        )

    def test_export_flat_day_view_multiple_quantity(self):
        self.data[VIEW] = DAY_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "multiple_deployment_flat_day_view.zip")

    def test_export_flat_day_view_single_quantity(self):
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "multiple_deployment_flat_day_view_single.zip")

    def test_export_flat_module_view_multiple_quantity(self):
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_module_view_multiple.zip"
        )

    def test_export_flat_module_view_single_quantity(self):
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_module_view_single.zip"
        )

    def test_export_flat_module_view_multiple_quantity_flat_structure(self):
        self.data[VIEW] = MODULE_VIEW
        self.data[LAYER] = FLAT_LAYER
        self.data[QUANTITY] = MULTIPLE_QTY
        self.data[ExportRequestObject.USE_FLAT_STRUCTURE] = True
        self.data[ExportRequestObject.INCLUDE_USER_META_DATA] = True
        self.data[ExportRequestObject.DEIDENTIFIED] = False
        self.data[FORMAT] = JSON_CSV_FORMAT
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_module_view_multiple_qty_flat_structure.zip"
        )

    def test_export_nested_module_view_multiple_quantity_with_org_id(self):
        """Test to confirm that only one deployment is exported even org id is provided"""
        self.data[VIEW] = MODULE_VIEW
        self.data[LAYER] = NESTED_LAYER
        self.data[FORMAT] = JSON_CSV_FORMAT
        self.data[ExportRequestObject.INCLUDE_USER_META_DATA] = True
        self.data[ExportRequestObject.DEIDENTIFIED] = False
        self.data[ExportRequestObject.ORGANIZATION_ID] = VALID_ORGANIZATION_ID
        self.data[ExportRequestObject.DEPLOYMENT_IDS] = [ORGANIZATION_DEPLOYMENT_ID]
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_module_view_multiple_qty_with_org.zip"
        )

    def test_export_nested_module_view_multiple_quantity_az_flat_structure(self):
        """Test to confirm that without flat structure we can see answers in metadata"""
        self.data[VIEW] = MODULE_VIEW
        self.data[LAYER] = NESTED_LAYER
        self.data[FORMAT] = JSON_CSV_FORMAT
        self.data[ExportRequestObject.INCLUDE_USER_META_DATA] = True
        self.data[ExportRequestObject.DEIDENTIFIED] = True
        self.data[ExportRequestObject.DEPLOYMENT_IDS] = [AZ_QUESTIONNAIRE_DEPLOYMENT]
        self.data[ExportRequestObject.USE_FLAT_STRUCTURE] = True
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp,
            "multiple_deployment_nested_module_view_multiple_qty_az_flat_structure.zip",
        )

        self.data[ExportRequestObject.USE_FLAT_STRUCTURE] = False
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp,
            "multiple_deployment_nested_module_view_multiple_qty_az_not_flat_structure.zip",
        )


class SingleFileResponseExportTestCase(MultiDeploymentExportTestCase):
    def setUp(self):
        super().setUp()
        self.data[ExportRequestObject.SINGLE_FILE_RESPONSE] = True

    def test_export_nested_module_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_jsons_are_equal(
            resp, "multiple_deployment_single_file_nested_module_view_single.json"
        )

    def test_export_nested_user_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = USER_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_jsons_are_equal(
            resp, "multiple_deployment_single_file_nested_user_view_single.json"
        )

    def test_export__nested_day_view_single_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_jsons_are_equal(
            resp, "multiple_deployment_single_file_nested_day_view_single.json"
        )

    def test_export_flat_day_view_multiple_quantity(self):
        self.data[LAYER] = FLAT_LAYER
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = MULTIPLE_QTY

        resp = self.request_export(self.data)
        self.assert_jsons_are_equal(
            resp, "multiple_deployment_single_file_flat_day_view_multiple.json"
        )

    def test_export_flat_day_view_multiple_quantity_csv(self):
        self.data[LAYER] = FLAT_LAYER
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = MULTIPLE_QTY
        self.data[FORMAT] = CSV_FORMAT

        resp = self.request_export(self.data)
        self.assert_jsons_are_equal(
            resp, "multiple_deployment_single_file_flat_day_view_multiple.csv"
        )

    def test_export_flat_day_view_multiple_quantity_csv_with_short_codes(self):
        self.data[LAYER] = FLAT_LAYER
        self.data[VIEW] = DAY_VIEW
        self.data[QUANTITY] = MULTIPLE_QTY
        self.data[FORMAT] = CSV_FORMAT
        self.data[PREFER_SHORT_CODE] = True

        resp = self.request_export(self.data)
        self.assert_jsons_are_equal(resp, "multiple_deployment_with_short_codes.csv")


class DeIdentifiedMultiDeploymentExportTestCase(MultiDeploymentExportTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.get_sample_request_data(
            deployment_ids=[ORGANIZATION_DEPLOYMENT_ID_2, ORGANIZATION_DEPLOYMENT_ID],
            deidentified=True,
        )

    def test_export_flat_module_view_deidentified(self):
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_module_view_deidentified.zip"
        )

    def test_export_nested_module_view_deidentified(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_nested_module_deidentified.zip"
        )

    def test_export_flat_user_view_single_deidentified(self):
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp, "multiple_deployment_flat_user_view_single_deidentified.zip"
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
            "multiple_deployment_nested_user_view_multiple_deidentified_with_binaries.zip",
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
            "multiple_deployment_flat_user_view_multiple_deidentified_with_binaries.zip",
        )

    def test_export_flat_module_view_multiple_deidentified_with_binaries(self):
        self.data[BINARY] = BINARY_INCLUDE
        self.data[FORMAT] = JSON_CSV_FORMAT
        self.data[VIEW] = MODULE_VIEW
        self.data[LAYER] = FLAT_LAYER
        self.data[ExportRequestObject.INCLUDE_USER_META_DATA] = True
        with patch.object(
            MinioFileStorageAdapter,
            "download_file",
            download_file_mock,
        ):
            resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp,
            "multiple_deployment_flat_module_json_csv_multiple_deidentified_with_binaries.zip",
        )
