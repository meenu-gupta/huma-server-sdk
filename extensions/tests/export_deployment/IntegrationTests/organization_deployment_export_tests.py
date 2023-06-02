from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.tests.export_deployment.IntegrationTests.export_deployment_router_tests import (
    ExportTestCase,
    LAYER,
    QUANTITY,
    VIEW,
    NESTED_LAYER,
    SINGLE_QTY,
    DAY_VIEW,
    MODULE_VIEW,
    BINARY_NONE,
)
from extensions.tests.export_deployment.IntegrationTests.export_permission_tests import (
    VALID_ORGANIZATION_ID,
)


class OrganizationExportTestCase(ExportTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.get_sample_request_data(organization_id=VALID_ORGANIZATION_ID)

    def test_export_nested_user_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_nested_user_view_multiple.zip")

    def test_export_flat_user_view_multiple_quantity(self):
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_flat_user_view_multiple.zip")

    def test_export_nested_day_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = DAY_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_nested_day_view_multiple.zip")

    def test_export_flat_day_view_multiple_quantity(self):
        self.data[VIEW] = DAY_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_flat_day_view_multiple.zip")

    def test_export_nested_module_view_multiple_quantity(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_nested_module_view_multiple.zip")

    def test_export_nested_module_view_single(self):
        self.data[LAYER] = NESTED_LAYER
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_nested_module_view_single.zip")

    def test_export_flat_module_view_single_quantity(self):
        self.data[VIEW] = MODULE_VIEW
        self.data[QUANTITY] = SINGLE_QTY
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_flat_module_view_single.zip")

    def test_export_flat_module_view_multiple_quantity(self):
        self.data[VIEW] = MODULE_VIEW
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(resp, "organization_flat_module_view_multiple.zip")

    def test_export_flat_module_view_including_and_excluding_fields(self):
        self.data[VIEW] = MODULE_VIEW
        self.data[ExportRequestObject.INCLUDE_USER_META_DATA] = True
        self.data[ExportRequestObject.INCLUDE_FIELDS] = [
            "user",
            "moduleId",
            "userId",
            "startDateTime",
        ]
        self.data[ExportRequestObject.EXCLUDE_FIELDS] = [
            "user.recentModuleResults",
            "user.roles.[*].roleId",
            "user.roles.[*].userType",
        ]
        org_id = self.data.pop(ExportRequestObject.ORGANIZATION_ID)
        self.create_export_profile(self.data, organization_id=org_id)
        resp = self.request_export(
            {
                ExportRequestObject.ORGANIZATION_ID: org_id,
                ExportRequestObject.BINARY_OPTION: BINARY_NONE,
            }
        )
        self.assert_zips_are_equal(
            resp,
            "multiple_deployment_flat_module_view_including_and_excluding_fields.zip",
        )

    def test_export_without_using_export_profile(self):
        self.data[ExportRequestObject.USE_EXPORT_PROFILE] = False
        resp = self.request_export(self.data)
        self.assert_zips_are_equal(
            resp,
            "multiple_deployment_flat_module_view_without_using_export_profile.zip",
        )
