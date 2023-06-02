from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import MagicMock

from extensions.appointment.exceptions import InvalidDateException
from extensions.appointment.models.appointment import Appointment
from extensions.appointment.router.appointment_requests import (
    CreateAppointmentRequestObject,
    UpdateAppointmentRequestObject,
    RetrieveAppointmentRequestObject,
    RetrieveAppointmentsRequestObject,
    DeleteAppointmentRequestObject,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.user import User
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import utc_str_field_to_val

SAMPLE_ID = "61e6538cfc477fd7f0ead871"

SAMPLE_APPOINTMENT_DICT = {
    Appointment.ID: SAMPLE_ID,
    Appointment.USER_ID: SAMPLE_ID,
    Appointment.MANAGER_ID: SAMPLE_ID,
    Appointment.STATUS: Appointment.Status.PENDING_CONFIRMATION,
    Appointment.START_DATE_TIME: utc_str_field_to_val(
        datetime.utcnow() + timedelta(days=1)
    ),
    Appointment.END_DATE_TIME: utc_str_field_to_val(
        datetime.utcnow() + timedelta(days=1, hours=1)
    ),
    Appointment.CREATE_DATE_TIME: utc_str_field_to_val(
        datetime.utcnow() + timedelta(days=1)
    ),
    Appointment.UPDATE_DATE_TIME: utc_str_field_to_val(
        datetime.utcnow() + timedelta(days=1, hours=1)
    ),
    Appointment.TITLE: "title",
    Appointment.DESCRIPTION: "description",
    Appointment.KEY_ACTION_ID: SAMPLE_ID,
    Appointment.CALL_ID: SAMPLE_ID,
    Appointment.NOTE_ID: SAMPLE_ID,
}


def get_time_with_timedelta(t_delta=timedelta(hours=1)):
    return utc_str_field_to_val(datetime.utcnow() + t_delta)


class TestCreateAppointmentRequestObject(TestCase):
    common_dict = {
        CreateAppointmentRequestObject.USER_ID: SAMPLE_ID,
        CreateAppointmentRequestObject.MANAGER_ID: SAMPLE_ID,
        CreateAppointmentRequestObject.START_DATE_TIME: get_time_with_timedelta(),
    }

    def test_success_create_appointment(self):
        try:
            CreateAppointmentRequestObject.from_dict(self.common_dict)
        except (ConvertibleClassValidationError, InvalidDateException):
            self.fail()

    def test_failure_with_past_date(self):
        with self.assertRaises(InvalidDateException) as context:
            CreateAppointmentRequestObject.from_dict(
                {
                    CreateAppointmentRequestObject.MANAGER_ID: SAMPLE_ID,
                    CreateAppointmentRequestObject.START_DATE_TIME: get_time_with_timedelta(
                        -timedelta(minutes=1)
                    ),
                    CreateAppointmentRequestObject.USER_ID: SAMPLE_ID,
                }
            )
        self.assertEqual(
            str(context.exception), "Schedule appointment for past is prohibited"
        )

    def test_failure_not_must_field(self):
        not_must_fields = [
            CreateAppointmentRequestObject.ID,
            CreateAppointmentRequestObject.CREATE_DATE_TIME,
            CreateAppointmentRequestObject.UPDATE_DATE_TIME,
            CreateAppointmentRequestObject.STATUS,
            UpdateAppointmentRequestObject.TITLE,
            UpdateAppointmentRequestObject.DESCRIPTION,
        ]
        for field in not_must_fields:
            with self.assertRaises(ConvertibleClassValidationError) as context:
                CreateAppointmentRequestObject.from_dict(
                    {**self.common_dict, field: SAMPLE_APPOINTMENT_DICT[field]}
                )
            self.assertEqual(str(context.exception), f"Keys should not exist: {field}")

    def test_failure_must_field(self):
        must_fields = [
            CreateAppointmentRequestObject.USER_ID,
            CreateAppointmentRequestObject.MANAGER_ID,
            CreateAppointmentRequestObject.START_DATE_TIME,
        ]
        for field in must_fields:
            with self.assertRaises(ConvertibleClassValidationError) as context:
                body = {**self.common_dict}
                body.pop(field, None)
                CreateAppointmentRequestObject.from_dict(body)
            self.assertEqual(str(context.exception), f"Missing keys: {field}")

    def test_failure_with_wrong_end_date_time(self):
        with self.assertRaises(InvalidDateException) as context:
            CreateAppointmentRequestObject.from_dict(
                {
                    **self.common_dict,
                    CreateAppointmentRequestObject.END_DATE_TIME: get_time_with_timedelta(
                        -timedelta(hours=1)
                    ),
                }
            )
        self.assertEqual(
            str(context.exception), "Start of the appointment can't be later than end."
        )


class TestUpdateAppointmentRequestObject(TestCase):
    common_dict = {
        UpdateAppointmentRequestObject.ID: SAMPLE_ID,
        UpdateAppointmentRequestObject.STATUS: Appointment.Status.SCHEDULED,
        UpdateAppointmentRequestObject.REQUESTER_ID: SAMPLE_ID,
        UpdateAppointmentRequestObject.IS_USER: True,
    }

    def test_success_for_user(self):
        try:
            UpdateAppointmentRequestObject.from_dict(self.common_dict)
        except (ConvertibleClassValidationError, InvalidDateException):
            self.fail()

    def test_success_for_manager(self):
        body = {
            **self.common_dict,
            UpdateAppointmentRequestObject.IS_USER: False,
            UpdateAppointmentRequestObject.USER_ID: SAMPLE_ID,
        }
        body.pop(UpdateAppointmentRequestObject.STATUS, None)
        try:
            UpdateAppointmentRequestObject.from_dict(body)
        except (ConvertibleClassValidationError, InvalidDateException):
            self.fail()

    def test_failure_without_requester_id(self):
        body = {**self.common_dict}
        body.pop(UpdateAppointmentRequestObject.REQUESTER_ID, None)
        with self.assertRaises(ConvertibleClassValidationError) as context:
            UpdateAppointmentRequestObject.from_dict({**body})
        self.assertEqual(
            str(context.exception),
            "Field [UpdateAppointmentRequestObject.requesterId] is mandatory",
        )

    def test_failure_with_past_date(self):
        with self.assertRaises(InvalidDateException) as context:
            UpdateAppointmentRequestObject.from_dict(
                {
                    UpdateAppointmentRequestObject.ID: SAMPLE_ID,
                    UpdateAppointmentRequestObject.REQUESTER_ID: SAMPLE_ID,
                    UpdateAppointmentRequestObject.USER_ID: SAMPLE_ID,
                    UpdateAppointmentRequestObject.IS_USER: False,
                    UpdateAppointmentRequestObject.START_DATE_TIME: get_time_with_timedelta(
                        -timedelta(minutes=1)
                    ),
                }
            )
        self.assertEqual(
            str(context.exception), "Schedule appointment for past is prohibited"
        )

    def test_failure_not_must_field(self):
        not_must_fields_for_manager = [
            UpdateAppointmentRequestObject.CREATE_DATE_TIME,
            UpdateAppointmentRequestObject.UPDATE_DATE_TIME,
            UpdateAppointmentRequestObject.KEY_ACTION_ID,
            UpdateAppointmentRequestObject.TITLE,
            UpdateAppointmentRequestObject.DESCRIPTION,
        ]
        not_must_fields_for_user = [
            *not_must_fields_for_manager,
            UpdateAppointmentRequestObject.USER_ID,
            UpdateAppointmentRequestObject.START_DATE_TIME,
            UpdateAppointmentRequestObject.END_DATE_TIME,
            UpdateAppointmentRequestObject.NOTE_ID,
            UpdateAppointmentRequestObject.CALL_ID,
        ]
        not_must_fields_for_manager.append(UpdateAppointmentRequestObject.STATUS)
        for field in not_must_fields_for_manager:
            with self.assertRaises(ConvertibleClassValidationError) as context:
                body = {
                    **self.common_dict,
                    UpdateAppointmentRequestObject.USER_ID: SAMPLE_ID,
                    UpdateAppointmentRequestObject.IS_USER: False,
                    field: SAMPLE_APPOINTMENT_DICT[field],
                }
                UpdateAppointmentRequestObject.from_dict(body)
            self.assertEqual(str(context.exception), f"Keys should not exist: {field}")

        for field in not_must_fields_for_user:
            with self.assertRaises(ConvertibleClassValidationError) as context:
                UpdateAppointmentRequestObject.from_dict(
                    {**self.common_dict, field: SAMPLE_APPOINTMENT_DICT[field]}
                )
            self.assertEqual(str(context.exception), f"Keys should not exist: {field}")

    def test_failure_must_field(self):
        must_fields_for_user = [
            UpdateAppointmentRequestObject.ID,
            UpdateAppointmentRequestObject.STATUS,
        ]
        must_fields_for_manager = [
            UpdateAppointmentRequestObject.ID,
            UpdateAppointmentRequestObject.USER_ID,
        ]

        for field in must_fields_for_user:
            with self.assertRaises(ConvertibleClassValidationError) as context:
                body = {**self.common_dict}
                body.pop(field, None)
                UpdateAppointmentRequestObject.from_dict(body)
            self.assertEqual(str(context.exception), f"Missing keys: {field}")

        for field in must_fields_for_manager:
            with self.assertRaises(ConvertibleClassValidationError) as context:
                body = {
                    **self.common_dict,
                    UpdateAppointmentRequestObject.IS_USER: False,
                }
                body.pop(field, None)
                UpdateAppointmentRequestObject.from_dict(body)
            self.assertEqual(str(context.exception), f"Missing keys: {field}")

    def test_failure_with_no_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            body = {**self.common_dict}
            body.pop(UpdateAppointmentRequestObject.ID, None)
            UpdateAppointmentRequestObject.from_dict(body)

    def test_failure_with_wrong_end_date_time(self):
        body = {
            **self.common_dict,
            UpdateAppointmentRequestObject.IS_USER: False,
            UpdateAppointmentRequestObject.USER_ID: SAMPLE_ID,
            UpdateAppointmentRequestObject.START_DATE_TIME: get_time_with_timedelta(),
            UpdateAppointmentRequestObject.END_DATE_TIME: get_time_with_timedelta(
                -timedelta(hours=1)
            ),
        }
        body.pop(UpdateAppointmentRequestObject.STATUS, None)
        with self.assertRaises(InvalidDateException) as context:
            UpdateAppointmentRequestObject.from_dict(body)
        self.assertEqual(
            str(context.exception), "Start of the appointment can't be later than end."
        )


class TestRetrieveAppointmentRequestObject(TestCase):
    def test_success(self):
        RetrieveAppointmentRequestObject.from_dict(
            {RetrieveAppointmentRequestObject.APPOINTMENT_ID: SAMPLE_ID}
        )

    def test_failure_with_invalid_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveAppointmentRequestObject.from_dict(
                {RetrieveAppointmentRequestObject.APPOINTMENT_ID: "invalid id"}
            )


class TestRetrieveAppointmentsRequestObject(TestCase):
    def test_success(self):
        try:
            RetrieveAppointmentsRequestObject.from_dict(
                {
                    RetrieveAppointmentsRequestObject.FROM_DATE_TIME: get_time_with_timedelta(),
                    RetrieveAppointmentsRequestObject.TO_DATE_TIME: get_time_with_timedelta(),
                    RetrieveAppointmentsRequestObject.REQUESTER_ID: SAMPLE_ID,
                    RetrieveAppointmentsRequestObject.USER_ID: SAMPLE_ID,
                }
            )
        except (ConvertibleClassValidationError, InvalidDateException):
            self.fail()

    def test_failure_with_invalid_requester_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveAppointmentsRequestObject.from_dict(
                {RetrieveAppointmentsRequestObject.REQUESTER_ID: "invalid id"}
            )


class TestDeleteAppointmentRequestObject(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind(binder):
            binder.bind(DefaultRoles, DefaultRoles())

        inject.clear_and_configure(bind)

    @classmethod
    def tearDownClass(cls) -> None:
        inject.clear()

    def test_success(self):
        try:
            DeleteAppointmentRequestObject.from_dict(
                {
                    DeleteAppointmentRequestObject.APPOINTMENT_ID: SAMPLE_ID,
                    DeleteAppointmentRequestObject.SUBMITTER: AuthorizedUser(
                        User(id="5eee34de4acf740d885767a8")
                    ),
                }
            )
        except (ConvertibleClassValidationError, InvalidDateException):
            self.fail()

    def test_failure_with_invalid_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            DeleteAppointmentRequestObject.from_dict(
                {DeleteAppointmentRequestObject.APPOINTMENT_ID: "invalid id"}
            )
