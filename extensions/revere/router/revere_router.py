from datetime import datetime

from flasgger import swag_from
from flask import jsonify, request, Response, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.common.policies import (
    get_user_route_read_policy,
)
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.module_result.modules.revere_test import RevereTestModule
from extensions.revere.models.revere import RevereTest, RevereTestResult
from extensions.revere.router.policies import (
    get_read_revere_tests_policy,
    get_write_revere_tests_policy,
)
from extensions.revere.router.revere_request_objects import (
    ProcessAudioResultRequestObject,
    ExportRevereResultsRequestObject,
)
from extensions.revere.service.revere_service import RevereTestService
from extensions.revere.use_cases.revere_use_case import UploadAudioResultUseCaseUseCase
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    validate_request_body_type_is_object,
)

api = IAMBlueprint(
    "revere_route",
    __name__,
    url_prefix="/api/extensions/v1beta/user",
    policy=get_user_route_read_policy,
)


@api.route("/<user_id>/revere-test/start/", methods=["POST"])
@api.require_policy(get_write_revere_tests_policy)
@swag_from(f"{SWAGGER_DIR}/start_test.yml")
def start_test(user_id):
    service = RevereTestService()
    deployment_id = str(AuthorizedUser(g.user).deployment_id())
    test_id, word_lists = service.create_test(
        user_id,
        deployment_id,
        RevereTestModule.moduleId,
    )
    return jsonify({"id": test_id, "wordLists": word_lists}), 201


@api.route(
    "/<user_id>/revere-test/<test_id>/words/<word_list_id>/audio/", methods=["POST"]
)
@api.require_policy(get_write_revere_tests_policy)
@swag_from(f"{SWAGGER_DIR}/process_audio.yml")
def upload_audio_result(user_id, test_id, word_list_id):
    data = validate_request_body_type_is_object(request)
    body = {
        **data,
        ProcessAudioResultRequestObject.USER_ID: user_id,
        ProcessAudioResultRequestObject.SUBMITTER_ID: user_id,
        ProcessAudioResultRequestObject.MODULE_ID: RevereTest.__name__,
        ProcessAudioResultRequestObject.TEST_ID: test_id,
        ProcessAudioResultRequestObject.ID: word_list_id,
    }
    req_obj = ProcessAudioResultRequestObject.from_dict(body)
    UploadAudioResultUseCaseUseCase().execute(req_obj)
    return "", 200


@api.route("/<user_id>/revere-test/<test_id>/finish/", methods=["POST"])
@api.require_policy(get_write_revere_tests_policy)
@swag_from(f"{SWAGGER_DIR}/finish_test.yml")
def finish_test(user_id, test_id):
    service = RevereTestService()
    service.finish_test(user_id, test_id)
    return "", 200


@api.route("/<user_id>/revere-test/all/", methods=["GET"])
@api.require_policy(get_read_revere_tests_policy)
@swag_from(f"{SWAGGER_DIR}/retrieve_user_tests.yml")
def retrieve_all_user_tests(user_id):
    service = RevereTestService()
    tests = service.retrieve_user_tests(user_id)
    tests_resp = [
        test.to_dict(
            ignored_fields=[
                RevereTest.ID,
                RevereTest.USER_ID,
                RevereTest.DEPLOYMENT_ID,
                f"{RevereTest.RESULTS}.{RevereTestResult.ID}",
                f"{RevereTest.RESULTS}.{RevereTestResult.USER_ID}",
                f"{RevereTest.RESULTS}.{RevereTestResult.DEPLOYMENT_ID}",
                f"{RevereTest.RESULTS}.{RevereTestResult.SUBMITTER_ID}",
            ]
        )
        for test in tests
    ]
    return jsonify(tests_resp), 200


@api.route("/<user_id>/revere-test/", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_users_finished_tests.yml")
def retrieve_finished_user_tests(user_id):
    service = RevereTestService()
    tests = service.retrieve_user_tests(user_id, RevereTest.Status.FINISHED.value)
    tests_resp = [
        test.to_dict(
            ignored_fields=[
                RevereTest.ID,
                RevereTest.USER_ID,
                RevereTest.DEPLOYMENT_ID,
                f"{RevereTest.RESULTS}.{RevereTestResult.ID}",
                f"{RevereTest.RESULTS}.{RevereTestResult.USER_ID}",
                f"{RevereTest.RESULTS}.{RevereTestResult.DEPLOYMENT_ID}",
                f"{RevereTest.RESULTS}.{RevereTestResult.SUBMITTER_ID}",
            ]
        )
        for test in tests
    ]
    return jsonify(tests_resp), 200


@api.route("/<user_id>/revere-test/<test_id>/", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/export_test_result.yml")
def export_test_result(user_id, test_id):
    service = RevereTestService()
    csv_data = service.export_test_result(user_id, test_id)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={test_id}.csv"},
    )


@api.route("/<user_id>/revere-test/export/", methods=["POST"])
@api.require_policy(get_write_revere_tests_policy)
def export_revere(user_id):
    data = validate_request_body_type_is_object(request)
    request_data = ExportRevereResultsRequestObject.from_dict(data)
    service = RevereTestService()
    data = service.export_tests_zip(user_id=user_id, status=request_data.status.value)

    return Response(
        data,
        mimetype="application/zip",
        headers={
            "Content-disposition": f"attachment; filename={user_id}_{datetime.now()}.zip"
        },
    )
