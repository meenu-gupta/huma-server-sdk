import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.dashboard.router.dashboard_router import (
    retrieve_dashboard,
    retrieve_dashboards,
    retrieve_gadget_data,
)

DASHBOARD_ROUTER_PATH = "extensions.dashboard.router.dashboard_router"

SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{DASHBOARD_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
class DashboardRouterTestCase(unittest.TestCase):
    @patch(f"{DASHBOARD_ROUTER_PATH}.replace_values")
    @patch(f"{DASHBOARD_ROUTER_PATH}.g")
    @patch(f"{DASHBOARD_ROUTER_PATH}.jsonify")
    @patch(f"{DASHBOARD_ROUTER_PATH}.RetrieveDashboardUseCase")
    @patch(f"{DASHBOARD_ROUTER_PATH}.RetrieveDashboardRequestObject")
    def test_success_retrieve_dashboard(
        self, req_obj, use_case, jsonify, g_mock, replace_values
    ):
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_dashboard("organization", SAMPLE_ID, SAMPLE_ID)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DASHBOARD_ID: SAMPLE_ID,
                    req_obj.RESOURCE_TYPE: "ORGANIZATION",
                    req_obj.RESOURCE_ID: SAMPLE_ID,
                    req_obj.SUBMITTER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            replace_values.assert_called_with(
                use_case().execute().value,
                g_mock.authz_user.localization,
                in_text_translation=True,
            )
            jsonify.assert_called_with(replace_values())

    @patch(f"{DASHBOARD_ROUTER_PATH}.replace_values")
    @patch(f"{DASHBOARD_ROUTER_PATH}.g")
    @patch(f"{DASHBOARD_ROUTER_PATH}.jsonify")
    @patch(f"{DASHBOARD_ROUTER_PATH}.RetrieveDashboardsUseCase")
    @patch(f"{DASHBOARD_ROUTER_PATH}.RetrieveDashboardsRequestObject")
    def test_success_retrieve_dashboards(
        self, req_obj, use_case, jsonify, g_mock, replace_values
    ):
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_dashboards("organization", SAMPLE_ID)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.RESOURCE_TYPE: "ORGANIZATION",
                    req_obj.RESOURCE_ID: SAMPLE_ID,
                    req_obj.SUBMITTER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            replace_values.assert_called_with(
                use_case().execute().value,
                g_mock.authz_user.localization,
                in_text_translation=True,
            )
            jsonify.assert_called_with(replace_values())

    @patch(f"{DASHBOARD_ROUTER_PATH}.replace_values")
    @patch(f"{DASHBOARD_ROUTER_PATH}.g")
    @patch(f"{DASHBOARD_ROUTER_PATH}.jsonify")
    @patch(f"{DASHBOARD_ROUTER_PATH}.RetrieveGadgetDataUseCase")
    @patch(f"{DASHBOARD_ROUTER_PATH}.RetrieveGadgetDataRequestObject")
    def test_success_retrieve_gadget_data(
        self, req_obj, use_case, jsonify, g_mock, replace_values
    ):
        body = {"a": "b"}
        gadget_id = "some_gadget_id"
        with testapp.test_request_context("/", json=body, method="POST") as _:
            retrieve_gadget_data("organization", SAMPLE_ID, gadget_id)
            req_obj.from_dict.assert_called_with(
                {
                    **body,
                    req_obj.GADGET_ID: gadget_id,
                    req_obj.ORGANIZATION_ID: SAMPLE_ID,
                    req_obj.RESOURCE_TYPE: "ORGANIZATION",
                    req_obj.RESOURCE_ID: SAMPLE_ID,
                    req_obj.SUBMITTER: g_mock.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            replace_values.assert_called_with(
                use_case().execute().value.to_dict(),
                g_mock.authz_user.localization,
                key_translation=True,
                in_text_translation=True,
            )
            jsonify.assert_called_with(replace_values())


if __name__ == "__main__":
    unittest.main()
