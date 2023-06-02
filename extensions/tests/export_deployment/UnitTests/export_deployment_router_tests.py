import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.export_deployment.models.export_deployment_models import ExportProcess
from extensions.export_deployment.router.export_deployment_routers import (
    retrieve_export_deployment_profiles,
    delete_export_profile,
    update_export_profile,
    create_export_profile,
    retrieve_export_deployment_processes,
    check_export_deployment_task_status,
    run_export_deployment_task,
    export,
    export_deployment,
)
from extensions.export_deployment.router.user_export_routers import (
    export_user_data_async,
)
from sdk.phoenix.audit_logger import AuditLog

EXPORT_DEPLOYMENT_ROUTER_PATH = (
    "extensions.export_deployment.router.export_deployment_routers"
)
USER_EXPORT_ROUTER_PATH = "extensions.export_deployment.router.user_export_routers"
SAMPLE_ID = "600a8476a961574fb38157d5"
PATH_USER_ID = "600a8476a961574fb38157d4"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class ExportDeploymentRouterTestCase(unittest.TestCase):
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.RetrieveExportProfilesRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.RetrieveExportProfilesUseCase")
    def test_success_retrieve_export_deployment_profiles(
        self, use_case, req_obj, jsonify
    ):
        with testapp.test_request_context("/", method="POST") as _:
            retrieve_export_deployment_profiles()
            req_obj.from_dict.assert_called_with({})
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.DeleteExportProfileRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.DeleteExportProfileUseCase")
    def test_success_delete_export_profile(self, use_case, req_obj):
        profile_id = SAMPLE_ID
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_export_profile(profile_id)
            req_obj.from_dict.assert_called_with({req_obj.PROFILE_ID: profile_id})
            use_case().execute(req_obj.from_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.UpdateExportProfileRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.UpdateExportProfileUseCase")
    def test_success_update_export_profile(self, use_case, req_obj, jsonify):
        profile_id = SAMPLE_ID
        with testapp.test_request_context("/", method="PUT") as _:
            update_export_profile(profile_id)
            req_obj.from_dict.assert_called_with({req_obj.ID: profile_id})
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.CreateExportProfileRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.CreateExportProfileUseCase")
    def test_success_create_export_profile(self, use_case, req_obj, jsonify):
        with testapp.test_request_context("/", method="POST") as _:
            create_export_profile()
            req_obj.from_dict.assert_called_with({})
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(
        f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.RetrieveExportDeploymentProcessesRequestObject"
    )
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.RetrieveExportDeploymentProcessesUseCase")
    def test_success_retrieve_export_deployment_processes(
        self, use_case, req_obj, jsonify
    ):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_export_deployment_processes(deployment_id)
            req_obj.from_dict.assert_called_with({req_obj.DEPLOYMENT_ID: deployment_id})
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(
        f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.CheckExportDeploymentTaskStatusRequestObject"
    )
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.CheckExportTaskStatusUseCase")
    def test_success_check_export_deployment_task_status(
        self, use_case, req_obj, jsonify
    ):
        deployment_id = SAMPLE_ID
        export_process_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            check_export_deployment_task_status(deployment_id, export_process_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.EXPORT_PROCESS_ID: export_process_id,
                    req_obj.DEPLOYMENT_ID: deployment_id,
                }
            )
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.g")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.jsonify")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.RunExportTaskRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.RunExportTaskUseCase")
    def test_success_run_export_deployment_task(
        self, use_case, req_obj, jsonify, g_mock
    ):
        deployment_id = SAMPLE_ID
        g_mock.user = MagicMock()
        g_mock.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            run_export_deployment_task(deployment_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.DEPLOYMENT_ID: deployment_id,
                    req_obj.REQUESTER_ID: g_mock.user.id,
                    req_obj.EXPORT_TYPE: ExportProcess.ExportType.DEFAULT.value,
                }
            )
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{USER_EXPORT_ROUTER_PATH}.g")
    @patch(f"{USER_EXPORT_ROUTER_PATH}.jsonify")
    @patch(f"{USER_EXPORT_ROUTER_PATH}.RunAsyncUserExportRequestObject")
    @patch(f"{USER_EXPORT_ROUTER_PATH}.AsyncExportUserDataUseCase")
    def test_success_run_user_export_task(self, use_case, req_obj, jsonify, g_mock):
        g_mock.user = MagicMock()
        g_mock.user.id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            export_user_data_async(PATH_USER_ID)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: PATH_USER_ID,
                    req_obj.REQUESTER_ID: g_mock.user.id,
                }
            )
            use_case().execute(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.BytesIO")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.send_file")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.make_response")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.ExportUsersRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.ExportDeploymentUseCase")
    def test_success_export(self, use_case, req_obj, make_response, send_file, BytesIO):
        payload = {"deploymentId": SAMPLE_ID}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            export()
            req_obj.from_dict.assert_called_with(
                {"deploymentId": "600a8476a961574fb38157d5"}
            )
            use_case().execute(req_obj.from_dict())

    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.BytesIO")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.send_file")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.make_response")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.ExportUsersRequestObject")
    @patch(f"{EXPORT_DEPLOYMENT_ROUTER_PATH}.ExportDeploymentUseCase")
    def test_success_export_deployment(
        self, use_case, req_obj, make_response, send_file, BytesIO
    ):
        deployment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            export_deployment(deployment_id)
            req_obj.from_dict.assert_called_with({req_obj.DEPLOYMENT_ID: deployment_id})
            use_case().execute(req_obj.from_dict())


if __name__ == "__main__":
    unittest.main()
