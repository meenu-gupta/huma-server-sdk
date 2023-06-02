import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from extensions.revere.models.revere import RevereTest
from extensions.revere.router.revere_router import (
    export_revere,
    export_test_result,
    retrieve_finished_user_tests,
    retrieve_all_user_tests,
    finish_test,
    upload_audio_result,
)
from sdk.phoenix.audit_logger import AuditLog

REVERE_ROUTER_PATH = "extensions.revere.router.revere_router"
REVERE_USE_CASES_PATH = "extensions.revere.use_cases.revere_use_case"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{REVERE_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch(f"{REVERE_ROUTER_PATH}.g", MagicMock())
@patch.object(AuditLog, "create_log", MagicMock())
class RevereRouterTestCase(unittest.TestCase):
    @patch(f"{REVERE_ROUTER_PATH}.ExportRevereResultsRequestObject")
    @patch(f"{REVERE_ROUTER_PATH}.RevereTestService")
    def test_success_export_revere(self, service, req_obj):
        user_id = SAMPLE_ID
        payload = {}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            export_revere(user_id)
            req_obj.from_dict.assert_called_with(payload)
            service().export_tests_zip.assert_called_with(
                user_id=user_id, status=req_obj.from_dict().status.value
            )

    @patch(f"{REVERE_ROUTER_PATH}.RevereTestService")
    def test_success_export_test_result(self, service):
        user_id = SAMPLE_ID
        test_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            export_test_result(user_id, test_id)
            service().export_test_result.assert_called_with(user_id, test_id)

    @patch(f"{REVERE_ROUTER_PATH}.RevereTestService")
    def test_success_retrieve_finished_user_tests(self, service):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_finished_user_tests(user_id)
            service().retrieve_user_tests.assert_called_with(
                user_id, RevereTest.Status.FINISHED.value
            )

    @patch(f"{REVERE_ROUTER_PATH}.RevereTestService")
    def test_success_retrieve_all_user_tests(self, service):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_all_user_tests(user_id)
            service().retrieve_user_tests.assert_called_with(user_id)

    @patch(f"{REVERE_ROUTER_PATH}.RevereTestService")
    def test_success_finish_test(self, service):
        user_id = SAMPLE_ID
        test_id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST") as _:
            finish_test(user_id, test_id)
            service().finish_test.assert_called_with(user_id, test_id)

    @patch(f"{REVERE_USE_CASES_PATH}.RevereTestResult")
    @patch(f"{REVERE_ROUTER_PATH}.ProcessAudioResultRequestObject")
    @patch(f"{REVERE_USE_CASES_PATH}.RevereTestService")
    def test_success_upload_audio_result(self, service, req_obj, result_object):
        payload = {}
        user_id = SAMPLE_ID
        test_id = SAMPLE_ID
        word_list_id = SAMPLE_ID
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            service().process_audio_result.return_value = [["some"], {}]
            upload_audio_result(user_id, test_id, word_list_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: SAMPLE_ID,
                    req_obj.MODULE_ID: "RevereTest",
                    req_obj.TEST_ID: SAMPLE_ID,
                    req_obj.ID: SAMPLE_ID,
                    req_obj.SUBMITTER_ID: SAMPLE_ID,
                }
            )
            service().process_audio_result.assert_called_with(
                req_obj.from_dict().audioResult
            )


if __name__ == "__main__":
    unittest.main()
