import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from bson import ObjectId
from freezegun import freeze_time

from extensions.appointment.component import AppointmentComponent
from extensions.appointment.exceptions import AppointmentErrorCodes
from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.mongo_appointment import MongoAppointment
from extensions.appointment.router.appointment_requests import (
    BulkDeleteAppointmentsRequestObject,
    RetrieveAppointmentsRequestObject,
    UpdateAppointmentRequestObject,
)
from extensions.appointment.router.appointment_response import (
    RetrieveAppointmentsResponseObject,
)
from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.key_action.component import KeyActionComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.repo.mongo_calendar_repository import MongoCalendarRepository
from sdk.calendar.router.calendar_request import ExportCalendarRequestObject
from sdk.calendar.tasks import prepare_events_and_execute, prepare_events_for_next_day
from sdk.common.exceptions.exceptions import ErrorCodes
from sdk.common.utils.validators import utc_str_field_to_val

VALID_USER_ID = "5e84b0dab8dfa268b1180536"
INVALID_USER_ID = "6e84b0dab8dfa268b1180532"

VALID_MANAGER1_ID = "5e8f0c74b50aa9656c34789c"
VALID_MANAGER2_ID = "5e8f0c74b50aa9656c34789a"
VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT = "6009a56a783a980cdcaa2b1c"
VALID_CUSTOM_ROLE = "6009a6072496f83856f06235"
VALID_CUSTOM_ROLE_WITH_OTHER_DEPLOYMENT = "6009a6072496f83856f06236"

VALID_APPOINTMENT_ID = "5eee34de4acf740d885767a8"
INVALID_APPOINTMENT_ID = "5eee34de4acf740d885767a7"

DEPLOYMENT_ID = "5d386cc6ff885918d96edb2c"
SEND_NOTIFICATION_ROUTE = (
    "extensions.appointment.models.appointment_event.AppointmentEvent.execute"
)


def stringify_date(date: datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def simple_appointment():
    return {
        Appointment.USER_ID: VALID_USER_ID,
        Appointment.START_DATE_TIME: stringify_date(
            datetime.utcnow() + timedelta(hours=4)
        ),
    }


class AppointmentRouterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        CalendarComponent(),
        AppointmentComponent(),
        ModuleResultComponent(),
        OrganizationComponent(),
        KeyActionComponent(),
    ]
    fixtures = [Path(__file__).parent.joinpath("fixtures/appointments_dump.json")]
    base_route = "/api/extensions/v1beta/user/{}/appointment"
    user_route = f"{base_route.format(VALID_USER_ID)}%s?deploymentId={DEPLOYMENT_ID}"
    manager_route = (
        f"{base_route.format(VALID_MANAGER1_ID)}%s?deploymentId={DEPLOYMENT_ID}"
    )

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.test_server.config.server.debugRouter = False
        self.headers = self.get_headers_for("User")

    def get_headers_for(self, role: str = "Admin", user_id: str = None):
        if not user_id:
            user_id = VALID_MANAGER1_ID if role == "Admin" else VALID_USER_ID
        return self.get_headers_for_token(user_id)

    def test_success_create_appointment_by_admin(self):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])

    def test_success_create_appointment_by_custom_role(self):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])

    def test_failre_create_appointment_by_custom_role_no_contact_patient_permission(
        self,
    ):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_create_appointment_user(self):
        rsp = self.flask_client.post(
            self.user_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_create_appointment_user_for_manager(self):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_failure_create_appointment_with_id_by_admin(self):
        body = {**simple_appointment(), Appointment.ID: "5e84b0dab8dfa268b1180536"}
        rsp = self.flask_client.post(
            self.manager_route % "", json=body, headers=self.get_headers_for("Admin")
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_appointment_with_id_by_custom_role(self):
        body = {**simple_appointment(), Appointment.ID: "5e84b0dab8dfa268b1180536"}
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_appointment_with_past_date_by_admin(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() - timedelta(days=1)
            ),
        }
        rsp = self.flask_client.post(
            self.manager_route % "", json=body, headers=self.get_headers_for("Admin")
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(AppointmentErrorCodes.INVALID_DATE, rsp.json["code"])

    def test_failure_create_appointment_with_past_date_by_custom_role(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() - timedelta(days=1)
            ),
        }
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(AppointmentErrorCodes.INVALID_DATE, rsp.json["code"])

    def test_failure_create_appointment_wrong_date_format_by_admin(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: "2020-16-17T20:16:00Z",
        }
        rsp = self.flask_client.post(
            self.manager_route % "", json=body, headers=self.get_headers_for("Admin")
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_create_appointment_wrong_date_format_by_custom_role(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: "2020-16-17T20:16:00Z",
        }
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_success_retrieve_appointment_by_admin(self):
        rsp = self.flask_client.get(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    def test_success_retrieve_appointment_by_custom_role(self):
        rsp = self.flask_client.get(
            f"{self.base_route.format(VALID_CUSTOM_ROLE)}/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    def test_failure_retrieve_appointment_by_custom_role_no_contact_patient_permission(
        self,
    ):
        rsp = self.flask_client.get(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_appointment_user(self):
        rsp = self.flask_client.get(
            self.user_route % f"/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    def test_failure_retrieve_appointment_invalid_id_by_admin(self):
        rsp = self.flask_client.get(
            self.manager_route % f"/{INVALID_APPOINTMENT_ID}",
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_failure_retrieve_appointment_invalid_id_by_custom_role_no_contact_patient_permission(
        self,
    ):
        rsp = self.flask_client.get(
            self.manager_route % f"/{INVALID_APPOINTMENT_ID}",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_appointments_by_admin(self):
        rsp = self.flask_client.get(
            self.user_route % "/search", headers=self.get_headers_for("Admin")
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            1, len(rsp.json[RetrieveAppointmentsResponseObject.Response.APPOINTMENTS])
        )

    def test_success_retrieve_appointments_by_custom_role(self):
        rsp = self.flask_client.get(
            f"{self.base_route.format(VALID_USER_ID)}/search",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            0, len(rsp.json[RetrieveAppointmentsResponseObject.Response.APPOINTMENTS])
        )

    def test_failure_retrieve_appointments_by_custom_role_no_contact_patient_permission(
        self,
    ):
        rsp = self.flask_client.get(
            self.user_route % "/search",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_success_retrieve_appointments_no_body_by_admin(self):
        rsp = self.flask_client.get(
            self.user_route % "/search", headers=self.get_headers_for("Admin")
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            1, len(rsp.json[RetrieveAppointmentsResponseObject.Response.APPOINTMENTS])
        )

    def test_failure_retrieve_appointments_no_body_by_custom_role_no_contact_patient_permission(
        self,
    ):
        rsp = self.flask_client.get(
            self.user_route % "/search",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_retrieve_appointments_by_user(self):
        rsp = self.flask_client.get(
            self.manager_route % "/search", headers=self.get_headers_for("User")
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(100004, rsp.json["code"])

    def test_success_retrieve_appointments_owner_user(self):
        rsp = self.flask_client.get(
            self.user_route % "/search", headers=self.get_headers_for("User")
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            2, len(rsp.json[RetrieveAppointmentsResponseObject.Response.APPOINTMENTS])
        )

    def test_success_retrieve_appointments_filtered(self):
        body = {
            RetrieveAppointmentsRequestObject.FROM_DATE_TIME: "2020-07-01T00:16:00Z",
            RetrieveAppointmentsRequestObject.TO_DATE_TIME: "2020-07-30T00:16:00Z",
        }
        rsp = self.flask_client.get(
            self.user_route % "/search",
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            1, len(rsp.json[RetrieveAppointmentsResponseObject.Response.APPOINTMENTS])
        )

        body = {
            RetrieveAppointmentsRequestObject.FROM_DATE_TIME: "2020-08-01T00:16:00Z",
            RetrieveAppointmentsRequestObject.TO_DATE_TIME: "2020-08-30T00:16:00Z",
        }
        rsp = self.flask_client.get(
            self.manager_route % "/search",
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            0, len(rsp.json[RetrieveAppointmentsResponseObject.Response.APPOINTMENTS])
        )

    def test_failure_retrieve_appointments_filtered_by_custom_role_no_contact_patient_permission(
        self,
    ):
        body = {
            RetrieveAppointmentsRequestObject.FROM_DATE_TIME: "2020-07-01T00:16:00Z",
            RetrieveAppointmentsRequestObject.TO_DATE_TIME: "2020-07-30T00:16:00Z",
        }
        rsp = self.flask_client.get(
            self.manager_route % "/search",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

        body = {
            RetrieveAppointmentsRequestObject.FROM_DATE_TIME: "2020-08-01T00:16:00Z",
            RetrieveAppointmentsRequestObject.TO_DATE_TIME: "2020-08-30T00:16:00Z",
        }
        rsp = self.flask_client.get(
            self.manager_route % "/search",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    @freeze_time("2020-07-16")
    def test_success_update_appointment_schedule_datetime(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(days=2)
            ),
        }
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for(),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    @freeze_time("2020-07-16")
    def test_success_update_appointment_schedule_datetime_with_no_start_date_time(self):
        body = {
            **simple_appointment(),
            Appointment.END_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(days=1)
            ),
        }
        body.pop(Appointment.START_DATE_TIME, None)
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for(),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    @freeze_time("2020-07-16")
    def test_success_update_appointment_schedule_datetime_by_custom_role(
        self,
    ):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(days=2)
            ),
        }
        manager_route = f"{self.base_route.format(VALID_CUSTOM_ROLE)}%s?deploymentId={DEPLOYMENT_ID}"
        rsp = self.flask_client.put(
            manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    @freeze_time("2020-07-16")
    def test_failure_update_appointment_by_custom_role_with_invalid_role(
        self,
    ):
        manager_route = f"{self.base_route.format(VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT)}/{VALID_APPOINTMENT_ID}"
        rsp = self.flask_client.put(
            manager_route,
            json=simple_appointment(),
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    @freeze_time("2020-07-16")
    def test_failure_update_appointment_by_custom_role_in_other_deployment(
        self,
    ):
        manager_route = f"{self.base_route.format(VALID_CUSTOM_ROLE_WITH_OTHER_DEPLOYMENT)}/{VALID_APPOINTMENT_ID}"
        rsp = self.flask_client.put(
            manager_route,
            json=simple_appointment(),
            headers=self.get_headers_for(
                user_id=VALID_CUSTOM_ROLE_WITH_OTHER_DEPLOYMENT
            ),
        )
        self.assertEqual(403, rsp.status_code)

    @freeze_time("2020-07-16")
    def test_failure_update_appointment_with_wrong_user_id(
        self,
    ):
        manager_route = (
            f"{self.base_route.format(VALID_CUSTOM_ROLE)}/{VALID_APPOINTMENT_ID}"
        )
        body = {
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(days=2)
            ),
            Appointment.USER_ID: "6009a56a783a980cdcaa2b1c",
        }
        rsp = self.flask_client.put(
            manager_route,
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual("Can't change assigned user", rsp.json["message"])

    def test_failure_update_appointment_schedule_datetime_by_custom_role_no_contact_patient_permission(
        self,
    ):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(days=2)
            ),
        }
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_appointment_schedule_datetime_wrong_format(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: "2020-16-17T20:16:00Z",
        }
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_failure_update_appointment_schedule_datetime_past_date(self):
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() - timedelta(days=1)
            ),
        }
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(400, rsp.status_code)
        self.assertEqual(110011, rsp.json["code"])

    @freeze_time("2020-07-16")
    def test_success_update_appointment_note(self):
        body = {**simple_appointment(), Appointment.NOTE_ID: VALID_APPOINTMENT_ID}
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    @freeze_time("2020-07-16")
    def test_success_update_appointment_note_by_custom_role(self):
        body = {**simple_appointment(), Appointment.NOTE_ID: VALID_APPOINTMENT_ID}
        rsp = self.flask_client.put(
            f"{self.base_route.format(VALID_CUSTOM_ROLE)}/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(VALID_APPOINTMENT_ID, rsp.json[Appointment.ID])

    def test_failure_update_appointment_note_by_custom_role_no_contact_patient_permission(
        self,
    ):
        body = {**simple_appointment(), Appointment.NOTE_ID: VALID_APPOINTMENT_ID}
        rsp = self.flask_client.put(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            json=body,
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_update_appointment_invalid_id(self):
        rsp = self.flask_client.put(
            self.manager_route % f"/{INVALID_APPOINTMENT_ID}",
            json=simple_appointment(),
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_success_delete_appointment(self):
        rsp = self.flask_client.delete(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(204, rsp.status_code)

    def test_success_delete_appointment_by_custom_role(self):
        rsp = self.flask_client.delete(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(204, rsp.status_code)

    def test_failure_delete_appointment_by_custom_role_no_contact_patient_permission(
        self,
    ):
        rsp = self.flask_client.delete(
            self.manager_route % f"/{VALID_APPOINTMENT_ID}",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE_NO_CONTACT_PATIENT),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_delete_appointment_invalid_id(self):
        rsp = self.flask_client.delete(
            self.manager_route % f"/{INVALID_APPOINTMENT_ID}",
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_failure_delete_appointment_invalid_id_by_custom_role(self):
        rsp = self.flask_client.delete(
            self.manager_route % f"/{INVALID_APPOINTMENT_ID}",
            headers=self.get_headers_for(user_id=VALID_CUSTOM_ROLE),
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_success_bulk_delete_appointments(self):
        body = {
            BulkDeleteAppointmentsRequestObject.APPOINTMENT_IDS: [VALID_APPOINTMENT_ID]
        }
        rsp = self.flask_client.delete(
            self.base_route.format(VALID_USER_ID),
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(1, rsp.json.get("deletedAppointments"))

    def test_failure_bulk_delete_appointments_containing_invalid_id(self):
        body = {
            BulkDeleteAppointmentsRequestObject.APPOINTMENT_IDS: [
                VALID_APPOINTMENT_ID,
                INVALID_APPOINTMENT_ID,
            ]
        }
        rsp = self.flask_client.delete(
            self.base_route.format(VALID_USER_ID),
            json=body,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_failure_export_calendar_with_appointment_debug_mode_off(self):
        query_params = {
            ExportCalendarRequestObject.START: "2020-01-01T00:00:00.000Z",
            ExportCalendarRequestObject.END: "2021-01-01T00:00:00.000Z",
        }
        rsp = self.flask_client.get(
            f"/api/calendar/v1beta/user/{VALID_USER_ID}/export",
            query_string=query_params,
        )
        self.assertEqual(401, rsp.status_code)

    @patch("sdk.common.push_notifications.push_notifications_utils.NotificationService")
    @patch("sdk.calendar.tasks.execute_events")
    @freeze_time("2022-01-28")
    def test_success_create_appointment_with_push_notification_and_key_action(
        self, mock_execute_events, mock_notification_service
    ):
        appointment = simple_appointment()
        appointment_date_time = "2022-01-28T00:00:00Z"
        appointment.update({Appointment.START_DATE_TIME: "2022-01-28T00:01:00Z"})
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=appointment,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])

        push = mock_notification_service().push_for_user
        push.assert_called_once()

        with freeze_time(appointment_date_time):
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_called_once()
            self.assertEqual(2, len(mock_execute_events.delay.call_args))
            appointment_dict = mock_execute_events.delay.call_args[0]
            self.assertIsNotNone(json.dumps(appointment_dict))

    @freeze_time("2020-07-17T21:26:00Z")
    def test_success_update_appointment_in_3_hours_accept(self):
        rsp = self.flask_client.put(
            self.user_route % f"/{VALID_APPOINTMENT_ID}",
            json={Appointment.STATUS: Appointment.Status.REJECTED.value},
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(200, rsp.status_code)

    def test_failure_update_appointment_in_3_hours_accept_to_reject(self):
        appointment = simple_appointment()
        start_date_time = datetime.utcnow() + timedelta(hours=5)
        appointment.update(
            {Appointment.START_DATE_TIME: utc_str_field_to_val(start_date_time)}
        )
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=appointment,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])
        created_id = rsp.json[Appointment.ID]

        rsp = self.flask_client.put(
            self.user_route % f"/{created_id}",
            json={Appointment.STATUS: Appointment.Status.SCHEDULED.value},
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(200, rsp.status_code)

        with freeze_time(datetime.utcnow() + timedelta(hours=3)):
            rsp = self.flask_client.put(
                self.user_route % f"/{created_id}",
                json={Appointment.STATUS: Appointment.Status.REJECTED.value},
                headers=self.get_headers_for("User"),
            )
            self.assertEqual(400, rsp.status_code)
            self.assertEqual(
                f"Appointment can not be updated in last {UpdateAppointmentRequestObject.BEFORE_HOURS} hours",
                rsp.json["message"],
            )

    @patch(SEND_NOTIFICATION_ROUTE)
    def test_success_check_key_action(self, mock_send_notification):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])
        created_id = rsp.json[Appointment.ID]
        mock_send_notification.assert_called_once()
        self.assertEqual(self._return_count_of_next_day_events(), 1)

        body = {Appointment.STATUS: Appointment.Status.REJECTED.value}
        self._test_update_status(self.user_route, created_id, body, 0)

        body = {Appointment.STATUS: Appointment.Status.SCHEDULED.value}
        self._test_update_status(self.user_route, created_id, body, 1)

        body = {
            Appointment.USER_ID: VALID_USER_ID,
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(hours=3)
            ),
        }
        self._test_update_status(
            self.manager_route, created_id, body, 1, self.get_headers_for()
        )
        name = MongoAppointment._collection.name
        collection = self.mongo_database[name]
        doc = collection.find_one({"_id": ObjectId(created_id)})
        self.assertEqual(
            Appointment.Status.PENDING_CONFIRMATION.value, doc[Appointment.STATUS]
        )

    def _test_update_status(
        self,
        route: str,
        appointment_id: str,
        body: dict,
        count_of_next_day_events: int,
        headers=None,
    ):
        rsp = self.flask_client.put(
            route % f"/{appointment_id}",
            json=body,
            headers=headers if headers else self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            count_of_next_day_events, self._return_count_of_next_day_events()
        )

    def _return_count_of_next_day_events(self, options=None):
        options = options if options else {}
        name = MongoCalendarRepository.CACHE_CALENDAR_COLLECTION
        collection = self.mongo_database[name]
        return collection.count_documents(options)

    @patch("sdk.calendar.tasks.execute_events")
    @freeze_time("2022-01-28")
    def test_success_reminder_before_an_hour(self, mock_execute_events):
        appointment = simple_appointment()
        appointment.update({Appointment.START_DATE_TIME: "2022-01-30T05:00:19.716Z"})
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=appointment,
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])
        created_id = rsp.json[Appointment.ID]

        rsp = self.flask_client.put(
            self.user_route % f"/{created_id}",
            json={Appointment.STATUS: Appointment.Status.SCHEDULED.value},
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(200, rsp.status_code)

        # Appointment reminder triggers at 2022-01-30T04:00:00Z so not happen at this time
        with freeze_time("2022-01-29T03:00:00Z"):
            prepare_events_for_next_day.apply()
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_not_called()

        with freeze_time("2022-01-30T04:00:00Z"):
            prepare_events_for_next_day.apply()
            prepare_events_and_execute.apply()
            mock_execute_events.delay.assert_called_once()
            self.assertEqual(2, len(mock_execute_events.delay.call_args))
            appointment_dict = mock_execute_events.delay.call_args[0]
            self.assertEqual("Appointment", appointment_dict[0][0]["type"])
            self.assertIsNotNone(json.dumps(appointment_dict))

    def test_success_create_and_update_delete_multiple_times(self):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        appointment_id = rsp.json[Appointment.ID]

        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: stringify_date(
                datetime.utcnow() + timedelta(days=1)
            ),
        }
        rsp = self.flask_client.put(
            self.manager_route % f"/{appointment_id}",
            json=body,
            headers=self.get_headers_for(),
        )
        self.assertEqual(200, rsp.status_code)

        new_start_date_time = stringify_date(datetime.utcnow() + timedelta(days=2))
        body = {
            **simple_appointment(),
            Appointment.START_DATE_TIME: new_start_date_time,
        }
        rsp = self.flask_client.put(
            self.manager_route % f"/{appointment_id}",
            json=body,
            headers=self.get_headers_for(),
        )
        self.assertEqual(200, rsp.status_code)

        rsp = self.flask_client.get(
            self.user_route % f"/{appointment_id}",
            headers=self.get_headers_for("User"),
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(
            rsp.json[Appointment.START_DATE_TIME], rsp.json[Appointment.END_DATE_TIME]
        )

        rsp = self.flask_client.delete(
            self.manager_route % f"/{appointment_id}",
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(204, rsp.status_code)

    def test_success_retrieve_appointment_key_actions_immediately(self):
        rsp = self.flask_client.post(
            self.manager_route % "",
            json=simple_appointment(),
            headers=self.get_headers_for("Admin"),
        )
        self.assertEqual(201, rsp.status_code)
        self.assertIsNotNone(rsp.json[Appointment.ID])

        rsp = self.flask_client.get(
            f"/api/extensions/v1beta/user/{VALID_USER_ID}/key-action",
            headers=self.get_headers_for("User", VALID_USER_ID),
        )
        self.assertEqual(1, len(rsp.json))
