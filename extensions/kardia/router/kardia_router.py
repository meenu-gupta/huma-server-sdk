from flasgger import swag_from
from flask import jsonify, request, g

from extensions.common.policies import (
    get_user_route_read_policy,
    get_user_route_write_policy,
)
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.kardia.models.kardia_integration_config import Action
from extensions.kardia.router.kardia_requests import (
    CreateKardiaPatientRequestObject,
    RetrievePatientRecordingsRequestObject,
    RetrieveSingleEcgRequestObject,
    RetrieveSingleEcgPdfRequestObject,
    SyncKardiaDataRequestObject,
)
from extensions.kardia.use_case.create_kardia_patient_use_case import (
    CreateKardiaPatientUseCase,
)
from extensions.kardia.use_case.retrieve_patient_recordings_use_case import (
    RetrievePatientRecordingsUseCase,
)
from extensions.kardia.use_case.retrieve_single_ecg_pdf_use_case import (
    RetrieveSingleEcgPdfUseCase,
)
from extensions.kardia.use_case.retrieve_single_ecg_use_case import (
    RetrieveSingleEcgUseCase,
)
from extensions.kardia.use_case.sync_kardia_data_use_case import SyncKardiaDataUseCase
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "kardia_router",
    __name__,
    url_prefix="/api/extensions/v1beta/kardia",
    policy=get_user_route_read_policy,
)


@api.route("/patient/<user_id>", methods=["POST"])
@api.require_policy(get_user_route_write_policy)
@audit(Action.CreateKardiaPatient)
@swag_from(f"{SWAGGER_DIR}/kardia_patient_create.yml")
def create_kardia_patient(user_id: str):
    body = get_request_json_dict_or_raise_exception(request)

    request_object = CreateKardiaPatientRequestObject.from_dict(
        {**remove_none_values(body), CreateKardiaPatientRequestObject.USER: g.user}
    )

    response = CreateKardiaPatientUseCase().execute(request_object)
    return jsonify(response.value), 200


@api.route("/recordings/<patient_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/patient_recordings_retrieve.yml")
def retrieve_patient_recordings(patient_id: str):
    request_object = RetrievePatientRecordingsRequestObject.from_dict(
        {RetrievePatientRecordingsRequestObject.PATIENT_ID: patient_id}
    )

    response = RetrievePatientRecordingsUseCase().execute(request_object)
    return jsonify(response.value), 200


@api.route("/ecg/<record_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/single_ecg_retrieve.yml")
def retrieve_single_ecg(record_id: str):
    request_object = RetrieveSingleEcgRequestObject.from_dict(
        {RetrieveSingleEcgRequestObject.RECORD_ID: record_id}
    )

    response = RetrieveSingleEcgUseCase().execute(request_object)

    return jsonify(response.value), 200


@api.route("/ecg-pdf/<user_id>/<record_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/single_ecg_pdf_retrieve.yml")
def retrieve_single_ecg_pdf(user_id: str, record_id: str):
    request_object = RetrieveSingleEcgPdfRequestObject.from_dict(
        {
            RetrieveSingleEcgPdfRequestObject.USER_ID: user_id,
            RetrieveSingleEcgPdfRequestObject.RECORD_ID: record_id,
            RetrieveSingleEcgPdfRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
        }
    )

    response = RetrieveSingleEcgPdfUseCase().execute(request_object)

    return jsonify(response.value), 200


@api.route("/sync/<user_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/sync_kardia_data.yml")
def sync_kardia_data(user_id: str):
    request_object = SyncKardiaDataRequestObject.from_dict(
        {
            SyncKardiaDataRequestObject.USER_ID: user_id,
            SyncKardiaDataRequestObject.DEPLOYMENT_ID: g.authz_user.deployment_id(),
        }
    )

    response = SyncKardiaDataUseCase().execute(request_object)
    return jsonify(response.value), 200
