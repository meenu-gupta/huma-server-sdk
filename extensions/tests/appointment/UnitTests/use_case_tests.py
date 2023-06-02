from copy import copy
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch
from extensions.appointment.use_case.bulk_delete_appointments_use_case import (
    BulkDeleteAppointmentsUseCase,
)

import i18n
from freezegun import freeze_time

from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.appointment_event import AppointmentEvent
from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from extensions.appointment.router.appointment_requests import (
    BulkDeleteAppointmentsRequestObject,
    CreateAppointmentRequestObject,
    UpdateAppointmentRequestObject,
    RetrieveAppointmentRequestObject,
    RetrieveAppointmentsRequestObject,
    DeleteAppointmentRequestObject,
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
)
from extensions.appointment.use_case.update_appointment_use_case import (
    UpdateAppointmentUseCase,
)
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User, RoleAssignment
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.utils import no_seconds
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRequestException
from sdk.common.localization.utils import Language, setup_i18n
from sdk.common.utils import inject
from sdk.common.utils.validators import utc_str_field_to_val as to_str

AUTHORIZATION_SERVICE_ROUTE = (
    "extensions.appointment.router.appointment_requests.AuthorizationService"
)
USE_CASE_ROUTE = "extensions.appointment.use_case"
SEND_NOTIFICATION_ROUTE = (
    "extensions.appointment.models.appointment_event.AppointmentEvent.execute"
)
SAMPLE_ID = "61e6538cfc477fd7f0ead871"
SAMPLE_USER_ID = "5e8f0c74b50aa9656c34789b"
SAMPLE_MANAGER_ID = "61f26b5d5af0e78952add5ae"

SAMPLE_APPOINTMENT_DICT = {
    Appointment.USER_ID: SAMPLE_USER_ID,
    Appointment.MANAGER_ID: SAMPLE_MANAGER_ID,
    Appointment.STATUS: Appointment.Status.PENDING_CONFIRMATION,
    Appointment.START_DATE_TIME: to_str(datetime.utcnow() + timedelta(days=1)),
    Appointment.END_DATE_TIME: to_str(datetime.utcnow() + timedelta(days=1, hours=1)),
    Appointment.TITLE: "title",
    Appointment.DESCRIPTION: "description",
    Appointment.KEY_ACTION_ID: SAMPLE_ID,
}

SAMPLE_APPOINTMENT: Appointment = Appointment.from_dict(SAMPLE_APPOINTMENT_DICT)


def get_appointment_with_status(
    status: Appointment.Status = Appointment.Status.SCHEDULED,
) -> Appointment:
    return Appointment.from_dict(
        {**SAMPLE_APPOINTMENT_DICT, Appointment.STATUS: status}
    )


class MockAuthUser:
    def __init__(self, user):
        self.user = user

    get_language = MagicMock()
    get_language.return_value = Language.EN


class MockCalendarService:
    create_calendar_event = MagicMock()
    update_calendar_event = MagicMock()
    delete_calendar_event = MagicMock()
    batch_delete_calendar_events_by_ids = MagicMock()


class MockAuthService:
    retrieve_user_profile = MagicMock()


class MockAppointmentRepo:
    create_appointment = MagicMock(return_value=SAMPLE_ID)
    update_appointment = MagicMock(return_value=SAMPLE_APPOINTMENT)
    retrieve_appointment = MagicMock(return_value=SAMPLE_APPOINTMENT)
    unset_key_action = MagicMock(return_value=SAMPLE_APPOINTMENT)
    retrieve_appointments = MagicMock(return_value=[])
    retrieve_appointments_by_ids = MagicMock(return_value=[SAMPLE_APPOINTMENT])
    delete_appointment = MagicMock()
    bulk_delete_appointments = MagicMock()


class MockAuthRepo:
    user = User(id=SAMPLE_ID)
    user.roles = [
        RoleAssignment(roleId="User", resource="deployment/5ff5b1059ba9a480d78481ef")
    ]
    retrieve_simple_user_profile = MagicMock(return_value=user)


class TestBaseAppointmentUseCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        CalendarEvent.register(Appointment.__name__, AppointmentEvent)
        CalendarEvent.register(AppointmentEvent.__name__, AppointmentEvent)
        loc_path = Path(__file__).parent.joinpath("./localization")
        i18n.translations.container = {}
        setup_i18n(str(loc_path))

    def setUp(self) -> None:
        self.appointment_repo = MockAppointmentRepo
        self.auth_repo = MockAuthRepo

        def bind(binder):
            binder.bind_to_provider(AppointmentRepository, self.appointment_repo)
            binder.bind_to_provider(AuthorizationRepository, self.auth_repo)

        inject.clear_and_configure(bind)

    def tearDown(self) -> None:
        MockCalendarService.create_calendar_event.reset_mock()
        MockCalendarService.update_calendar_event.reset_mock()
        MockCalendarService.delete_calendar_event.reset_mock()


class TestCreateAppointmentUseCase(TestBaseAppointmentUseCase):
    @patch(f"{USE_CASE_ROUTE}.create_appointment_use_case.AuthorizedUser", MockAuthUser)
    @patch(
        f"{USE_CASE_ROUTE}.create_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    @patch(SEND_NOTIFICATION_ROUTE)
    @freeze_time("2022-01-27")
    def test_success_create_appointment(self, mock_send_notification):
        start_datetime = datetime.utcnow() + timedelta(hours=1)
        str_start_datetime = to_str(start_datetime)
        request_object = CreateAppointmentRequestObject.from_dict(
            {
                CreateAppointmentRequestObject.MANAGER_ID: SAMPLE_MANAGER_ID,
                CreateAppointmentRequestObject.START_DATE_TIME: str_start_datetime,
                CreateAppointmentRequestObject.USER_ID: SAMPLE_USER_ID,
            }
        )

        self.appointment_repo.create_appointment.return_value = SAMPLE_ID
        use_case = CreateAppointmentUseCase(auth_repo=MagicMock())
        use_case.execute(request_object)
        mock_send_notification.assert_called_once()
        expected_event = AppointmentEvent.from_dict(
            {
                AppointmentEvent.MODEL: Appointment.__name__,
                AppointmentEvent.TITLE: "New appointment request",
                AppointmentEvent.DESCRIPTION: "Please respond to the appointment request from your care team",
                AppointmentEvent.START_DATE_TIME: "2022-01-27T00:00:00.000000Z",
                AppointmentEvent.END_DATE_TIME: str_start_datetime,
                AppointmentEvent.USER_ID: SAMPLE_USER_ID,
                AppointmentEvent.APPOINTMENT_DATE_TIME: str_start_datetime,
                AppointmentEvent.APPOINTMENT_ID: SAMPLE_ID,
                AppointmentEvent.APPOINTMENT_STATUS: Appointment.Status.PENDING_CONFIRMATION.value,
            }
        )
        MockCalendarService.create_calendar_event.assert_called_with(expected_event)

    @patch(
        f"{USE_CASE_ROUTE}.create_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    @patch("sdk.common.push_notifications.push_notifications_utils.NotificationService")
    def test_success_test_push_notification(self, mock_notification_service):
        start_datetime = datetime.utcnow() + timedelta(minutes=1)
        str_start_datetime = to_str(start_datetime)
        request_object = CreateAppointmentRequestObject.from_dict(
            {
                CreateAppointmentRequestObject.MANAGER_ID: SAMPLE_MANAGER_ID,
                CreateAppointmentRequestObject.START_DATE_TIME: str_start_datetime,
                CreateAppointmentRequestObject.USER_ID: SAMPLE_USER_ID,
            }
        )
        CreateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)
        push = mock_notification_service().push_for_user
        push.assert_called_once()


class TestUpdateAppointmentUseCase(TestBaseAppointmentUseCase):
    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    @patch(f"{USE_CASE_ROUTE}.update_appointment_use_case.Event")
    @patch(f"{USE_CASE_ROUTE}.update_appointment_use_case.RetrieveAppointmentUseCase")
    def test_success_update_appointment_when_accepted(self, mock_use_case, event):
        next_status = Appointment.Status.SCHEDULED
        request_object = UpdateAppointmentRequestObject.from_dict(
            {
                UpdateAppointmentRequestObject.REQUESTER_ID: SAMPLE_USER_ID,
                UpdateAppointmentRequestObject.ID: SAMPLE_ID,
                UpdateAppointmentRequestObject.IS_USER: True,
                UpdateAppointmentRequestObject.STATUS: next_status,
            }
        )
        appointment = Appointment.from_dict(
            {
                **SAMPLE_APPOINTMENT_DICT,
                Appointment.STATUS: next_status.value,
                Appointment.ID: SAMPLE_ID,
            }
        )
        self.appointment_repo.update_appointment.return_value = appointment
        mock_use_case().execute().value = Appointment.from_dict(
            {
                **SAMPLE_APPOINTMENT_DICT,
                Appointment.STATUS: Appointment.Status.PENDING_CONFIRMATION,
                Appointment.ID: SAMPLE_ID,
            }
        )
        UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)
        MockCalendarService.create_calendar_event.assert_called_once()
        reminder_time = no_seconds(appointment.startDateTime - timedelta(hours=1))
        event.from_dict.assert_called_with(
            {
                event.MODEL: Appointment.__name__,
                event.TITLE: "Attend scheduled appointment",
                event.DESCRIPTION: "Scheduled appointment",
                event.START_DATE_TIME: to_str(reminder_time),
                event.END_DATE_TIME: to_str(appointment.endDateTime),
                event.USER_ID: SAMPLE_USER_ID,
                event.APPOINTMENT_DATE_TIME: to_str(appointment.startDateTime),
                event.APPOINTMENT_ID: SAMPLE_ID,
                event.APPOINTMENT_STATUS: Appointment.Status.SCHEDULED.value,
            }
        )
        event.from_dict().execute.assert_not_called()

    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    @patch(SEND_NOTIFICATION_ROUTE)
    def test_success_update_appointment_with_same_status(self, mock_send_notification):
        request_object = UpdateAppointmentRequestObject.from_dict(
            {
                UpdateAppointmentRequestObject.REQUESTER_ID: SAMPLE_USER_ID,
                UpdateAppointmentRequestObject.USER_ID: SAMPLE_USER_ID,
                UpdateAppointmentRequestObject.ID: SAMPLE_ID,
                UpdateAppointmentRequestObject.IS_USER: False,
            }
        )
        self.appointment_repo.update_appointment.return_value = SAMPLE_APPOINTMENT
        UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)
        mock_send_notification.assert_not_called()
        MockCalendarService.create_calendar_event.assert_not_called()

    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    @patch(f"{USE_CASE_ROUTE}.update_appointment_use_case.Event")
    def test_success_reschedule_appointment(self, event):
        old_appointment = get_appointment_with_status(Appointment.Status.SCHEDULED)
        old_appointment.id = SAMPLE_ID
        self.appointment_repo.retrieve_appointment.return_value = old_appointment

        now = datetime.utcnow()
        new_start_date_time = now + timedelta(hours=12)
        data = {
            UpdateAppointmentRequestObject.REQUESTER_ID: SAMPLE_USER_ID,
            UpdateAppointmentRequestObject.USER_ID: SAMPLE_USER_ID,
            UpdateAppointmentRequestObject.ID: SAMPLE_ID,
            UpdateAppointmentRequestObject.IS_USER: False,
            UpdateAppointmentRequestObject.START_DATE_TIME: to_str(new_start_date_time),
        }
        request_object = UpdateAppointmentRequestObject.from_dict(data)
        updated_appointment = get_appointment_with_status(
            Appointment.Status.PENDING_CONFIRMATION
        )
        updated_appointment.id = SAMPLE_ID
        updated_appointment.startDateTime = request_object.startDateTime
        self.appointment_repo.update_appointment.return_value = updated_appointment
        with freeze_time(now):
            UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)
            event.from_dict.assert_called_with(
                {
                    event.MODEL: Appointment.__name__,
                    event.TITLE: "title",
                    event.DESCRIPTION: "description",
                    event.START_DATE_TIME: to_str(no_seconds(now)),
                    event.END_DATE_TIME: to_str(old_appointment.endDateTime),
                    event.USER_ID: SAMPLE_USER_ID,
                    event.APPOINTMENT_DATE_TIME: to_str(request_object.startDateTime),
                    event.APPOINTMENT_ID: SAMPLE_ID,
                    event.APPOINTMENT_STATUS: Appointment.Status.PENDING_CONFIRMATION.value,
                }
            )
        event.from_dict().execute.assert_called_once()
        MockCalendarService.delete_calendar_event.assert_called_once()

    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    def test_success_update_appointment_when_rejected(self):
        next_status = Appointment.Status.REJECTED
        request_object = self._get_request_object(next_status)
        self.appointment_repo.retrieve_appointment.return_value = (
            get_appointment_with_status(Appointment.Status.SCHEDULED)
        )
        self.appointment_repo.update_appointment.return_value = (
            get_appointment_with_status(Appointment.Status.REJECTED)
        )
        UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)
        MockCalendarService.delete_calendar_event.assert_called_once()

    @staticmethod
    def _get_request_object(status, is_user=True):
        return UpdateAppointmentRequestObject.from_dict(
            {
                UpdateAppointmentRequestObject.REQUESTER_ID: SAMPLE_USER_ID,
                UpdateAppointmentRequestObject.ID: SAMPLE_ID,
                UpdateAppointmentRequestObject.IS_USER: is_user,
                UpdateAppointmentRequestObject.STATUS: status,
            }
        )

    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    def test_failure_update_appointment_when_time_expired(self):
        next_status = Appointment.Status.REJECTED
        request_object = self._get_request_object(next_status)
        old_appointment = get_appointment_with_status(Appointment.Status.SCHEDULED)
        old_appointment.startDateTime = datetime.utcnow() + timedelta(hours=1)
        self.appointment_repo.retrieve_appointment.return_value = old_appointment
        self.appointment_repo.update_appointment.return_value = (
            get_appointment_with_status(Appointment.Status.REJECTED)
        )
        with self.assertRaises(InvalidRequestException) as context:
            UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)

        self.assertEqual(
            str(context.exception),
            f"Appointment can not be updated in last {UpdateAppointmentUseCase.BEFORE_HOURS} hours",
        )

    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    def test_failure_update_appointment_when_user_is_invalid(self):
        next_status = Appointment.Status.REJECTED
        request_object = self._get_request_object(next_status)
        old_appointment = get_appointment_with_status(Appointment.Status.SCHEDULED)
        old_appointment.userId = SAMPLE_ID
        self.appointment_repo.retrieve_appointment.return_value = old_appointment
        self.appointment_repo.update_appointment.return_value = (
            get_appointment_with_status(Appointment.Status.REJECTED)
        )
        with self.assertRaises(InvalidRequestException) as context:
            UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)

        self.assertEqual(str(context.exception), "Can't change assigned user")

    @patch(
        f"{USE_CASE_ROUTE}.update_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    def test_failure_update_appointment_with_invalid_status(self):
        next_status = Appointment.Status.PENDING_CONFIRMATION

        request_object = self._get_request_object(next_status)

        self.appointment_repo.retrieve_appointment.return_value = (
            get_appointment_with_status(Appointment.Status.SCHEDULED)
        )
        self.appointment_repo.update_appointment.return_value = (
            get_appointment_with_status(Appointment.Status.PENDING_CONFIRMATION)
        )
        with self.assertRaises(InvalidRequestException) as context:
            UpdateAppointmentUseCase(auth_repo=MagicMock()).execute(request_object)

        self.assertEqual(
            str(context.exception),
            f"Update appointment with next status [%s] is not allowed for the current status [%s]"
            % (next_status.name, Appointment.Status.SCHEDULED.name),
        )


class TestRetrieveAppointmentUseCase(TestBaseAppointmentUseCase):
    def test_success(self):
        request_object = RetrieveAppointmentRequestObject.from_dict(
            {RetrieveAppointmentRequestObject.APPOINTMENT_ID: SAMPLE_ID}
        )
        RetrieveAppointmentUseCase().execute(request_object)
        self.appointment_repo.retrieve_appointment.assert_called_with(SAMPLE_ID)


class TestRetrieveAppointmentsUseCase(TestBaseAppointmentUseCase):
    def test_success(self):
        request_object = RetrieveAppointmentsRequestObject.from_dict(
            {
                RetrieveAppointmentsRequestObject.REQUESTER_ID: SAMPLE_ID,
                RetrieveAppointmentsRequestObject.USER_ID: SAMPLE_ID,
            }
        )
        RetrieveAppointmentsUseCase().execute(request_object)
        self.appointment_repo.retrieve_appointments.assert_called_with(
            SAMPLE_ID, SAMPLE_ID, None, None
        )


class TestDeleteAppointmentUseCase(TestBaseAppointmentUseCase):
    @patch(
        f"{USE_CASE_ROUTE}.delete_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    def test_success(self):
        request_object = DeleteAppointmentRequestObject.from_dict(
            {
                DeleteAppointmentRequestObject.APPOINTMENT_ID: SAMPLE_ID,
                DeleteAppointmentRequestObject.SUBMITTER: AuthorizedUser(
                    MockAuthRepo().retrieve_simple_user_profile()
                ),
            }
        )
        DeleteAppointmentUseCase().execute(request_object)
        MockCalendarService().delete_calendar_event.assert_called_once_with(SAMPLE_ID)

    @patch(
        f"{USE_CASE_ROUTE}.delete_appointment_use_case.CalendarService",
        MockCalendarService,
    )
    def test_failure(self):
        user = copy(MockAuthRepo().retrieve_simple_user_profile())
        user.roles = [
            RoleAssignment(
                roleId="User", resource="deployment/5ff5b1059ba9a480d7848aaa"
            )
        ]
        request_object = DeleteAppointmentRequestObject.from_dict(
            {
                DeleteAppointmentRequestObject.APPOINTMENT_ID: SAMPLE_ID,
                DeleteAppointmentRequestObject.SUBMITTER: AuthorizedUser(user),
            }
        )
        with self.assertRaises(PermissionDenied):
            DeleteAppointmentUseCase().execute(request_object)


class TestBulkDeleteAppointmentsUseCase(TestBaseAppointmentUseCase):
    @patch(
        f"{USE_CASE_ROUTE}.bulk_delete_appointments_use_case.CalendarService",
        MockCalendarService,
    )
    def test_success(self):
        request_object = BulkDeleteAppointmentsRequestObject.from_dict(
            {
                BulkDeleteAppointmentsRequestObject.APPOINTMENT_IDS: [SAMPLE_ID],
                BulkDeleteAppointmentsRequestObject.USER_ID: SAMPLE_USER_ID,
                BulkDeleteAppointmentsRequestObject.SUBMITTER: AuthorizedUser(
                    MockAuthRepo().retrieve_simple_user_profile()
                ),
            }
        )
        BulkDeleteAppointmentsUseCase().execute(request_object)
        self.appointment_repo.bulk_delete_appointments.assert_called_once_with(
            [SAMPLE_ID]
        )
        MockCalendarService().batch_delete_calendar_events_by_ids.assert_called_once()

    @patch(
        f"{USE_CASE_ROUTE}.bulk_delete_appointments_use_case.CalendarService",
        MockCalendarService,
    )
    def test_failure(self):
        user = copy(MockAuthRepo().retrieve_simple_user_profile())
        user.roles = [
            RoleAssignment(
                roleId="User", resource="deployment/5ff5b1059ba9a480d7848aaa"
            )
        ]
        request_object = BulkDeleteAppointmentsRequestObject.from_dict(
            {
                BulkDeleteAppointmentsRequestObject.APPOINTMENT_IDS: [SAMPLE_ID],
                BulkDeleteAppointmentsRequestObject.USER_ID: SAMPLE_USER_ID,
                BulkDeleteAppointmentsRequestObject.SUBMITTER: AuthorizedUser(user),
            }
        )
        with self.assertRaises(PermissionDenied):
            BulkDeleteAppointmentsUseCase().execute(request_object)
