from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.tests.export_deployment.IntegrationTests.export_deployment_router_tests import (
    ExportTestCase,
    ORGANIZATION_USER_ID,
)
from sdk.common.utils.validators import remove_none_values

OTHER_ORGANIZATION_ID = "5d386cc6ff885918d96eda1b"
VALID_ORGANIZATION_ID = "5d386cc6ff885918d96eda1a"
ORGANIZATION_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
OTHER_DEPLOYMENT_ID = "5d386cc6ff885918d96edb2d"
ORG_DEPLOYMENT_USER = "5e8f0c74b50aa9656c34789c"
MULTI_DEPLOYMENT_USER_ID = "5e8f0c74b50aa9656c34789d"


def get_sample_request_data(
    organization_id: str = None,
    deployment_id: str = None,
    deployment_ids: list[str] = None,
    deidentified: bool = True,
):
    request_data = {
        ExportRequestObject.VIEW: ExportRequestObject.DataViewOption.USER.value,
        ExportRequestObject.BINARY_OPTION: ExportRequestObject.BinaryDataOption.NONE.value,
        ExportRequestObject.LAYER: ExportRequestObject.DataLayerOption.FLAT.value,
        ExportRequestObject.QUANTITY: ExportRequestObject.DataQuantityOption.SINGLE.value,
        ExportRequestObject.DEPLOYMENT_ID: deployment_id,
        ExportRequestObject.DEPLOYMENT_IDS: deployment_ids,
        ExportRequestObject.ORGANIZATION_ID: organization_id,
        ExportRequestObject.DEIDENTIFIED: deidentified,
    }
    return remove_none_values(request_data)


class ExportPermissionsTestCase(ExportTestCase):
    override_config = {
        "server.exportDeployment.enableAuthz": "true",
        "server.exportDeployment.enableAuth": "true",
    }
    API_URL = f"/api/extensions/v1beta/export/"

    def test_export_organization_id_allowed_only_for_same_organization(self):
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        data = get_sample_request_data(organization_id=VALID_ORGANIZATION_ID)
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(200, resp.status_code)

        data = get_sample_request_data(organization_id=OTHER_ORGANIZATION_ID)
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

    def test_export_deployment_ids_allowed_only_if_user_has_same_deployments(self):
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        data = get_sample_request_data(deployment_ids=[ORGANIZATION_DEPLOYMENT_ID])
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(200, resp.status_code)

        data = get_sample_request_data(
            deployment_ids=[ORGANIZATION_DEPLOYMENT_ID, OTHER_DEPLOYMENT_ID]
        )
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

    def test_export_deployment_id_allowed_only_if_user_has_same_deployment_and_permissions(
        self,
    ):
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        data = get_sample_request_data(deployment_id=ORGANIZATION_DEPLOYMENT_ID)
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(200, resp.status_code)

        data = get_sample_request_data(deployment_id=OTHER_DEPLOYMENT_ID)
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

        headers = self.get_headers_for_token(ORG_DEPLOYMENT_USER)
        data = get_sample_request_data(deployment_id=ORGANIZATION_DEPLOYMENT_ID)
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

    def test_export_organization_id_without_view_identifier_permission_fails(self):
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        data = get_sample_request_data(
            organization_id=VALID_ORGANIZATION_ID, deidentified=False
        )
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

    def test_export_deployment_ids_without_view_identifier_permission_fails(self):
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        data = get_sample_request_data(
            deployment_ids=[ORGANIZATION_DEPLOYMENT_ID], deidentified=False
        )
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

    def test_export_deployment_id_without_view_identifier_permission_fails(
        self,
    ):
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        data = get_sample_request_data(
            deployment_id=ORGANIZATION_DEPLOYMENT_ID, deidentified=False
        )
        resp = self.flask_client.post(self.API_URL, headers=headers, json=data)
        self.assertEqual(403, resp.status_code)

    def test_export_user_data_permissions(
        self,
    ):
        user_url = f"{self.API_URL}user/{MULTI_DEPLOYMENT_USER_ID}"
        headers = self.get_headers_for_token(MULTI_DEPLOYMENT_USER_ID)
        request_data = {
            ExportRequestObject.BINARY_OPTION: ExportRequestObject.BinaryDataOption.NONE.value
        }
        resp = self.flask_client.post(user_url, json=request_data, headers=headers)
        self.assertEqual(200, resp.status_code)

        # another user cannot export
        headers = self.get_headers_for_token(ORG_DEPLOYMENT_USER)
        resp = self.flask_client.post(user_url, json=request_data, headers=headers)
        self.assertEqual(403, resp.status_code)

        # manager with proper permissions cannot export
        headers = self.get_headers_for_token(ORGANIZATION_USER_ID)
        resp = self.flask_client.post(user_url, json=request_data, headers=headers)
        self.assertEqual(403, resp.status_code)
