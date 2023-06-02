import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.module_result.router.module_result_router import (
    create_module_result,
    retrieve_module_result,
    retrieve_aggregated,
    search_module_results,
    retrieve_module_results,
)
from extensions.tests.module_result.IntegrationTests.test_samples import (
    sample_fjs_hip_score_data,
)
from sdk.common.utils.json_utils import replace_values
from sdk.phoenix.audit_logger import AuditLog

MODULE_RESULT_ROUTER_PATH = "extensions.module_result.router.module_result_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{MODULE_RESULT_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class ModuleResultsRouterTestCase(unittest.TestCase):
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.jsonify")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.RetrieveModuleResultUseCase")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.RetrieveModuleResultRequestObject")
    def test_success_retrieve_module_result(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        primitive_type = "primitive_type"
        module_result_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_module_result(user_id, primitive_type, module_result_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: user_id,
                    req_obj.MODULE_RESULT_ID: module_result_id,
                    req_obj.PRIMITIVE_TYPE: primitive_type,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{MODULE_RESULT_ROUTER_PATH}.jsonify")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.ModuleResultService")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.AggregateModuleResultsRequestObjects")
    def test_success_retrieve_aggregated(self, req_obj, service, jsonify):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            retrieve_aggregated(user_id)
            req_obj.from_dict.assert_called_with({req_obj.USER_ID: user_id})
            service().retrieve_aggregated_results.assert_called_with(
                primitive_name=req_obj.from_dict().primitiveName,
                module_config_id=req_obj.from_dict().moduleConfigId,
                aggregation_function=req_obj.from_dict().function,
                mode=req_obj.from_dict().mode,
                start_date=req_obj.from_dict().fromDateTime,
                end_date=req_obj.from_dict().toDateTime,
                skip=req_obj.from_dict().skip,
                limit=req_obj.from_dict().limit,
                user_id=req_obj.from_dict().userId,
                timezone=req_obj.from_dict().timezone,
            )
            jsonify.assert_called_with(service().retrieve_aggregated_results())

    @patch(f"{MODULE_RESULT_ROUTER_PATH}.jsonify")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.SearchModuleResultsUseCase")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.SearchModuleResultsRequestObject")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.g")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}._convert_primitives")
    def test_success_search_module_results(
        self, convert_primitives, g_mock, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.get_role.return_value = MagicMock()
        g_mock.authz_user.get_role.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            search_module_results(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: user_id,
                    req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                    req_obj.ROLE: g_mock.authz_user.get_role().id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            convert_primitives.assert_called_with(use_case().execute().value)
            jsonify.assert_called_with(convert_primitives())

    @patch(f"{MODULE_RESULT_ROUTER_PATH}.jsonify")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.ModuleResultService")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.RetrieveModuleResultsRequestObject")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.g")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}._convert_primitives")
    def test_success_retrieve_module_results(
        self, convert_primitives, g_mock, req_obj, service, jsonify
    ):
        user_id = SAMPLE_ID
        module_id = SAMPLE_ID
        g_mock.authz_user = MagicMock()
        g_mock.authz_user.get_role.return_value = MagicMock()
        g_mock.authz_user.get_role.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            retrieve_module_results(user_id, module_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: user_id,
                    req_obj.MODULE_ID: module_id,
                    req_obj.DEPLOYMENT_ID: g_mock.authz_user.deployment_id(),
                    req_obj.ROLE: g_mock.authz_user.get_role().id,
                }
            )
            service().retrieve_module_results.assert_called_with(
                req_obj.from_dict().userId,
                req_obj.from_dict().moduleId,
                req_obj.from_dict().skip,
                req_obj.from_dict().limit,
                req_obj.from_dict().direction,
                req_obj.from_dict().fromDateTime,
                req_obj.from_dict().toDateTime,
                req_obj.from_dict().filters,
                req_obj.from_dict().deploymentId,
                req_obj.from_dict().role,
                req_obj.from_dict().excludedFields,
                req_obj.from_dict().moduleConfigId,
                req_obj.from_dict().excludeModuleIds,
                req_obj.from_dict().unseenOnly,
            )
            convert_primitives.assert_called_with(service().retrieve_module_results())
            jsonify.assert_called_with(
                replace_values(convert_primitives(), g_mock.authz_user.localization)
            )

    @patch(f"{MODULE_RESULT_ROUTER_PATH}.jsonify")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.ModuleResultService")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.CreateModuleResultRequestObject")
    @patch(f"{MODULE_RESULT_ROUTER_PATH}.g")
    def test_success_create_module_result(
        self, mock_g, mock_req_obj, mock_svc, mock_jsonify
    ):
        user_id = SAMPLE_ID
        module_id = SAMPLE_ID
        mock_g.user = MagicMock()
        data = sample_fjs_hip_score_data()
        with testapp.test_request_context("/", json=[data], method="POST") as _:
            create_module_result(user_id, module_id)
            mock_req_obj.from_dict.assert_called_once()
            mock_svc.return_value.create_module_result.assert_called_once()
            mock_jsonify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
