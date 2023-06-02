from flasgger import swag_from
from flask import request, jsonify, g

from extensions.common.policies import (
    get_user_route_read_policy,
    get_user_route_write_policy,
)
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.medication.models.medication import Action
from extensions.medication.router.medication_request import (
    CreateMedicationRequestObject,
    UpdateMedicationRequestObject,
    RetrieveMedicationsRequestObject,
)
from extensions.medication.use_case.create_medication_use_case import (
    CreateMedicationUseCase,
)
from extensions.medication.use_case.retrieve_medications_use_case import (
    RetrieveMedicationsUseCase,
)
from extensions.medication.use_case.update_medication_use_case import (
    UpdateMedicationUseCase,
)
from extensions.module_result.modules import MedicationsModule

from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.phoenix.audit_logger import audit

api = IAMBlueprint(
    "medication_route",
    __name__,
    url_prefix="/api/extensions/v1beta/user",
    policy=get_user_route_read_policy,
)


@api.route("/<user_id>/medication/", methods=["POST"])
@api.require_policy(get_user_route_write_policy)
@audit(Action.CreateMedication)
@swag_from(f"{SWAGGER_DIR}/create_medication.yml")
def create_medication(user_id: str):
    medication_dict = get_request_json_dict_or_raise_exception(request)
    medication_dict.update({"userId": user_id})

    request_object = CreateMedicationRequestObject.from_dict(medication_dict)
    request_object.enabled = True
    if not request_object.moduleId:
        request_object.moduleId = MedicationsModule.moduleId
    if not request_object.deploymentId:
        request_object.deploymentId = g.authz_user.deployment_id()

    response = CreateMedicationUseCase().execute(request_object)
    return jsonify({"id": response.value}), 201


@api.route("/<user_id>/medication/retrieve", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/retrieve_medication.yml")
def retrieve_medications(user_id: str):
    request_dict = get_request_json_dict_or_raise_exception(request)
    request_dict.update({RetrieveMedicationsRequestObject.USER_ID: user_id})

    request_object: RetrieveMedicationsRequestObject = (
        RetrieveMedicationsRequestObject.from_dict(request_dict)
    )

    response_obj = RetrieveMedicationsUseCase().execute(request_object)
    result = response_obj.medication_to_dict(response_obj.value)
    return jsonify(result), 200


@api.route("/<user_id>/medication/<medication_id>", methods=["POST"])
@api.require_policy(get_user_route_write_policy)
@audit(Action.UpdateMedication, target_key="medication_id")
@swag_from(f"{SWAGGER_DIR}/update_medication.yml")
def update_medication(user_id: str, medication_id: str):
    medication_dict = get_request_json_dict_or_raise_exception(request)
    medication_dict.update({"userId": user_id, "id": medication_id})

    request_object = UpdateMedicationRequestObject.from_dict(medication_dict)

    response = UpdateMedicationUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200
