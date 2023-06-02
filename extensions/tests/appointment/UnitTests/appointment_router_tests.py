import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from flask import Flask

from extensions.appointment.models.appointment import Appointment
from extensions.appointment.router.appointment_requests import (
    DEFAULT_APPOINTMENT_RESULT_PAGE_SIZE,
)
from extensions.appointment.router.appointment_router import (
    delete_appointment,
    update_appointment,
    retrieve_appointments,
    retrieve_appointment,
    create_appointment,
    retrieve_appointments_get,
)
from sdk.phoenix.audit_logger import AuditLog

APPOINTMENT_ROUTER_PATH = "extensions.appointment.router.appointment_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


@patch(
    f"{APPOINTMENT_ROUTER_PATH}.IAMBlueprint.get_endpoint_policies",
    MagicMock(return_value=[]),
)
@patch.object(AuditLog, "create_log", MagicMock())
class AppointmentRouterTestCase(unittest.TestCase):
    @patch(f"{APPOINTMENT_ROUTER_PATH}.DeleteAppointmentUseCase")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.DeleteAppointmentRequestObject")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.g")
    def test_success_delete_appointment(self, mock_g, req_obj, use_case):
        user_id = SAMPLE_ID
        appointment_id = SAMPLE_ID
        mock_g.authz_user = MagicMock()
        with testapp.test_request_context("/", method="DELETE") as _:
            delete_appointment(user_id, appointment_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.APPOINTMENT_ID: appointment_id,
                    req_obj.SUBMITTER: mock_g.authz_user,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())

    @patch(f"{APPOINTMENT_ROUTER_PATH}.g")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.jsonify")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.UpdateAppointmentUseCase")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.UpdateAppointmentRequestObject")
    def test_success_update_appointment(self, req_obj, use_case, jsonify, mock_g):
        user_id = SAMPLE_ID
        appointment_id = SAMPLE_ID
        mock_g.authz_path_user = MagicMock()
        mock_g.authz_path_user.is_user.return_value = True
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            update_appointment(user_id, appointment_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.REQUESTER_ID: user_id,
                    req_obj.ID: appointment_id,
                    req_obj.IS_USER: True,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})

    @patch(f"{APPOINTMENT_ROUTER_PATH}.jsonify")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.RetrieveAppointmentsUseCase")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.RetrieveAppointmentsRequestObject")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.g")
    def test_success_retrieve_appointments(self, g_mock, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        g_mock.auth_user = MagicMock()
        g_mock.auth_user.is_user.return_value = True
        type(g_mock.auth_user).id = PropertyMock(return_value=user_id)
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            retrieve_appointments(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    req_obj.REQUESTER_ID: g_mock.auth_user.id,
                    req_obj.USER_ID: user_id,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with([])

    @patch(f"{APPOINTMENT_ROUTER_PATH}.jsonify")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.RetrieveAppointmentsUseCaseV1")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.RetrieveAppointmentsGetRequestObject")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.g")
    def test_success_retrieve_appointments_get(
        self, g_mock, req_obj, use_case, jsonify
    ):
        user_id = SAMPLE_ID
        g_mock.auth_user = MagicMock()
        g_mock.auth_user.is_user.return_value = True
        type(g_mock.auth_user).id = PropertyMock(return_value=user_id)
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="PUT", json=payload) as _:
            retrieve_appointments_get(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    req_obj.USER_ID: user_id,
                    req_obj.REQUESTER_ID: g_mock.auth_user.id,
                    req_obj.SKIP: 0,
                    req_obj.LIMIT: DEFAULT_APPOINTMENT_RESULT_PAGE_SIZE,
                }
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{APPOINTMENT_ROUTER_PATH}.jsonify")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.RetrieveAppointmentUseCase")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.RetrieveAppointmentRequestObject")
    def test_success_retrieve_appointment(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        appointment_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            retrieve_appointment(user_id, appointment_id)
            req_obj.from_dict.assert_called_with(
                {req_obj.APPOINTMENT_ID: appointment_id}
            )
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with(use_case().execute().value.to_dict())

    @patch(f"{APPOINTMENT_ROUTER_PATH}.jsonify")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.CreateAppointmentUseCase")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.CreateAppointmentRequestObject")
    @patch(f"{APPOINTMENT_ROUTER_PATH}.g", MagicMock())
    def test_success_create_appointment(self, req_obj, use_case, jsonify):
        user_id = SAMPLE_ID
        payload = {"a": "b"}
        with testapp.test_request_context("/", method="POST", json=payload) as _:
            create_appointment(user_id)
            req_obj.from_dict.assert_called_with(
                {
                    **payload,
                    Appointment.MANAGER_ID: user_id,
                }
            )
            use_case().check_permission = MagicMock(return_value=True)
            use_case().execute.assert_called_with(req_obj.from_dict())
            jsonify.assert_called_with({"id": use_case().execute().value})


if __name__ == "__main__":
    unittest.main()
