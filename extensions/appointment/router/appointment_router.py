from extensions.appointment.use_case.bulk_delete_appointments_use_case import (
    BulkDeleteAppointmentsUseCase,
)
from flasgger import swag_from
from flask import request, jsonify, g

from extensions.appointment.models.appointment import Appointment, AppointmentAction
from extensions.appointment.router.appointment_requests import (
    BulkDeleteAppointmentsRequestObject,
    RetrieveAppointmentsRequestObject,
    UpdateAppointmentRequestObject,
    RetrieveAppointmentRequestObject,
    DeleteAppointmentRequestObject,
    CreateAppointmentRequestObject,
    RetrieveAppointmentsGetRequestObject,
    DEFAULT_APPOINTMENT_RESULT_PAGE_SIZE,
)
from extensions.appointment.use_case.create_appointment_use_case import (
    CreateAppointmentUseCase,
)
from extensions.appointment.use_case.delete_appointment_use_case import (
    DeleteAppointmentUseCase,
)
from extensions.appointment.use_case.retrieve_appointment_use_case import (
    RetrieveAppointmentUseCase,
)
from extensions.appointment.use_case.retrieve_appointments_use_case import (
    RetrieveAppointmentsUseCase,
    RetrieveAppointmentsUseCaseV1,
)
from extensions.appointment.use_case.update_appointment_use_case import (
    UpdateAppointmentUseCase,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.router.policies import get_read_policy
from extensions.common.policies import (
    get_user_route_read_policy,
    get_update_appointment_policy,
)
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
    validate_request_body_type_is_object,
)
from sdk.common.utils.validators import remove_none_values

from sdk.phoenix.audit_logger import audit

appointment_route = IAMBlueprint(
    "appointment_route",
    __name__,
    url_prefix="/api/extensions/v1beta/user",
    policy=get_user_route_read_policy,
)


@appointment_route.route("/<user_id>/appointment", methods=["POST"])
@appointment_route.require_policy(PolicyType.SCHEDULE_AND_CALL_PATIENT)
@audit(AppointmentAction.CreateAppointment)
@swag_from(f"{SWAGGER_DIR}/create_appointment.yml")
def create_appointment(user_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object: CreateAppointmentRequestObject = (
        CreateAppointmentRequestObject.from_dict(
            {**body, Appointment.MANAGER_ID: user_id}
        )
    )
    request_object.check_permission(g.authz_user)
    response = CreateAppointmentUseCase().execute(request_object)
    return jsonify({"id": response.value}), 201


@appointment_route.route("/<user_id>/appointment/<appointment_id>", methods=["GET"])
@appointment_route.require_policy(get_read_policy)
@swag_from(f"{SWAGGER_DIR}/retrieve_appointment.yml")
def retrieve_appointment(user_id, appointment_id):
    request_object = RetrieveAppointmentRequestObject.from_dict(
        {RetrieveAppointmentRequestObject.APPOINTMENT_ID: appointment_id}
    )
    response = RetrieveAppointmentUseCase().execute(request_object)
    return jsonify(response.value.to_dict(include_none=False)), 200


@appointment_route.route("/<user_id>/appointment/search", methods=["PUT"])
@appointment_route.require_policy(get_read_policy)
@swag_from(f"{SWAGGER_DIR}/retrieve_appointments.yml")
def retrieve_appointments(user_id):
    body = validate_request_body_type_is_object(request)
    body.update(
        {
            RetrieveAppointmentsRequestObject.REQUESTER_ID: g.auth_user.id,
            RetrieveAppointmentsRequestObject.USER_ID: user_id,
        }
    )
    req = RetrieveAppointmentsRequestObject.from_dict(body)

    response = RetrieveAppointmentsUseCase().execute(req)
    return (
        jsonify([i.to_dict(include_none=False) for i in response.value]),
        200,
    )


@appointment_route.get("/<user_id>/appointment/search")
@appointment_route.require_policy(get_read_policy)
@swag_from(f"{SWAGGER_DIR}/retrieve_appointments_v1.yml")
def retrieve_appointments_get(user_id):
    args = request.args or {}
    skip = int(args.get(RetrieveAppointmentsGetRequestObject.SKIP, 0))
    limit = int(
        args.get(
            RetrieveAppointmentsGetRequestObject.LIMIT,
            DEFAULT_APPOINTMENT_RESULT_PAGE_SIZE,
        )
    )
    request_object = RetrieveAppointmentsGetRequestObject.from_dict(
        {
            RetrieveAppointmentsGetRequestObject.USER_ID: user_id,
            RetrieveAppointmentsGetRequestObject.REQUESTER_ID: g.auth_user.id,
            RetrieveAppointmentsGetRequestObject.SKIP: skip,
            RetrieveAppointmentsGetRequestObject.LIMIT: limit,
        }
    )

    response = RetrieveAppointmentsUseCaseV1().execute(request_object)
    return jsonify(response.value.to_dict(include_none=False)), 200


@appointment_route.route("/<user_id>/appointment/<appointment_id>", methods=["PUT"])
@appointment_route.require_policy(get_update_appointment_policy)
@audit(AppointmentAction.UpdateAppointment, target_key="appointment_id")
@swag_from(f"{SWAGGER_DIR}/update_appointment.yml")
def update_appointment(user_id, appointment_id):
    body = get_request_json_dict_or_raise_exception(request)
    authz_path_user: AuthorizedUser = g.authz_path_user

    request_object = UpdateAppointmentRequestObject.from_dict(
        {
            **body,
            UpdateAppointmentRequestObject.REQUESTER_ID: user_id,
            UpdateAppointmentRequestObject.ID: appointment_id,
            UpdateAppointmentRequestObject.IS_USER: authz_path_user.is_user(),
        }
    )
    request_object.check_permission(g.authz_user)
    response = UpdateAppointmentUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@appointment_route.route("/<user_id>/appointment/<appointment_id>", methods=["DELETE"])
@appointment_route.require_policy(PolicyType.RESCHEDULE_CALL)
@audit(AppointmentAction.DeleteAppointment, target_key="appointment_id")
@swag_from(f"{SWAGGER_DIR}/delete_appointment.yml")
def delete_appointment(user_id, appointment_id):
    request_object = DeleteAppointmentRequestObject.from_dict(
        {
            DeleteAppointmentRequestObject.APPOINTMENT_ID: appointment_id,
            DeleteAppointmentRequestObject.SUBMITTER: g.authz_user,
        }
    )
    DeleteAppointmentUseCase().execute(request_object)
    return "", 204


@appointment_route.delete("/<user_id>/appointment")
@appointment_route.require_policy(PolicyType.RESCHEDULE_CALL)
@audit(AppointmentAction.BulkDeleteAppointments)
@swag_from(f"{SWAGGER_DIR}/bulk_delete_appointments.yml")
def bulk_delete_appointments(user_id):
    body = get_request_json_dict_or_raise_exception(request)
    request_object = BulkDeleteAppointmentsRequestObject.from_dict(
        {
            **body,
            BulkDeleteAppointmentsRequestObject.USER_ID: user_id,
            BulkDeleteAppointmentsRequestObject.SUBMITTER: g.authz_user,
        }
    )
    response_object = BulkDeleteAppointmentsUseCase().execute(request_object)
    return jsonify(response_object.value), 200
