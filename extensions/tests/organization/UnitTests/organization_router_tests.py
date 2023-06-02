import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from extensions.organization.router.organization_router import (
    retrieve_organizations,
    unlink_deployment,
    link_deployment,
    delete_organization,
    update_organization,
    retrieve_organization,
    create_organization,
    link_deployments,
    unlink_deployments,
)
from sdk.phoenix.audit_logger import AuditLog

ORGANIZATION_ROUTER_PATH = "extensions.organization.router.organization_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{ORGANIZATION_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class OrganizationRouterTestCase(unittest.TestCase):
    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.RetrieveOrganizationsUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.RetrieveOrganizationsRequestObject")
    def test_success_retrieve_organizations(self, req_obj, use_case, jsonify):
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            retrieve_organizations()
            req_obj.from_dict.assert_called_with(payload)
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value)

    @patch(f"{ORGANIZATION_ROUTER_PATH}.UnlinkDeploymentUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.UnlinkDeploymentRequestObject")
    def test_success_unlink_deployment(self, req_obj, use_case):
        organization_id = SAMPLE_ID
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            unlink_deployment(organization_id, deployment_id)
            req_obj.assert_called_with(
                organizationId=organization_id, deploymentId=deployment_id
            )
            use_case().execute.assert_called_with(req_obj())

    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.LinkDeploymentUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.LinkDeploymentRequestObject")
    def test_success_link_deployment(self, req_obj, use_case, jsonify):
        organization_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            link_deployment(organization_id)
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.ORGANIZATION_ID: organization_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({req_obj.ID: use_case().execute().value})

    @patch(f"{ORGANIZATION_ROUTER_PATH}.DeleteOrganizationUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.DeleteOrganizationRequestObject")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.g")
    def test_success_delete_organization(self, g_mock, req_obj, use_case):
        g_mock.user = MagicMock(id=SAMPLE_ID)
        organization_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_organization(organization_id)
            expected_call = {
                req_obj.ORGANIZATION_ID: organization_id,
                req_obj.SUBMITTER_ID: SAMPLE_ID,
            }
            req_obj.from_dict.assert_called_with(expected_call)
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.UpdateOrganizationUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.UpdateOrganizationRequestObject")
    def test_success_update_organization(self, req_obj, use_case, jsonify):
        organization_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            update_organization(organization_id)
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.ID: organization_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({req_obj.ID: use_case().execute().value})

    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.RetrieveOrganizationUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.RetrieveOrganizationRequestObject")
    def test_success_retrieve_organization(self, req_obj, use_case, jsonify):
        organization_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_organization(organization_id)
            req_obj.from_dict.assert_called_with(
                {req_obj.ORGANIZATION_ID: organization_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.CreateOrganizationUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.CreateOrganizationRequestObject")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.g")
    def test_success_create_organization(self, g_mock, req_obj, use_case, jsonify):
        g_mock.user = MagicMock(id=SAMPLE_ID)
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_organization()
            req_obj.from_dict.assert_called_with(
                {**payload, req_obj.SUBMITTER_ID: SAMPLE_ID}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({req_obj.ID: use_case().execute().value})

    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.LinkDeploymentsUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.LinkDeploymentsRequestObject")
    def test_success_link_deployments(self, req_obj, use_case, jsonify):
        organization_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            link_deployments(organization_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.ORGANIZATION_ID: organization_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({req_obj.ID: use_case().execute().value})

    @patch(f"{ORGANIZATION_ROUTER_PATH}.jsonify")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.UnlinkDeploymentsUseCase")
    @patch(f"{ORGANIZATION_ROUTER_PATH}.UnlinkDeploymentsRequestObject")
    def test_success_unlink_deployments(self, req_obj, use_case, jsonify):
        organization_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            unlink_deployments(organization_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.ORGANIZATION_ID: organization_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({req_obj.ID: use_case().execute().value})


if __name__ == "__main__":
    unittest.main()
