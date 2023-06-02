from datetime import datetime

from extensions.appointment.models.appointment import Appointment
from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.policies import are_users_in_the_same_resource
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
    positive_integer_field,
    natural_number_field,
)
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import (
    must_not_be_present,
    must_be_present,
    validate_datetime,
    utc_str_val_to_field,
    validate_object_id,
    validate_object_ids,
)


DEFAULT_APPOINTMENT_RESULT_PAGE_SIZE = 20


@convertibleclass
class CreateAppointmentRequestObject(Appointment):
    @classmethod
    def validate(cls, appointment):
        must_not_be_present(
            id=appointment.id,
            title=appointment.title,
            description=appointment.description,
            updateDateTime=appointment.updateDateTime,
            createDateTime=appointment.createDateTime,
            status=appointment.status,
        )

        must_be_present(
            userId=appointment.userId,
            managerId=appointment.managerId,
            startDateTime=appointment.startDateTime,
        )
        appointment.validate_date_times()

    def post_init(self):
        self.status = Appointment.Status.PENDING_CONFIRMATION
        self.endDateTime = self.endDateTime or self.startDateTime
        self.createDateTime = self.updateDateTime = datetime.utcnow()

    @autoparams("repo")
    def check_permission(
        self, submitter: AuthorizedUser, repo: AuthorizationRepository
    ):
        user = repo.retrieve_simple_user_profile(user_id=self.userId)
        authz_user = AuthorizedUser(user)
        if not are_users_in_the_same_resource(authz_user, submitter):
            raise PermissionDenied


@convertibleclass
class RetrieveAppointmentRequestObject:
    APPOINTMENT_ID = "appointmentId"

    appointmentId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveAppointmentsRequestObject:
    FROM_DATE_TIME = "fromDateTime"
    TO_DATE_TIME = "toDateTime"
    REQUESTER_ID = "requesterId"
    USER_ID = "userId"

    _datetime_meta = meta(validate_datetime, value_to_field=utc_str_val_to_field)

    requesterId: str = required_field(metadata=meta(validate_object_id))
    fromDateTime: datetime = default_field(metadata=_datetime_meta)
    toDateTime: datetime = default_field(metadata=_datetime_meta)
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveAppointmentsGetRequestObject:
    SKIP = "skip"
    LIMIT = "limit"
    REQUESTER_ID = "requesterId"
    USER_ID = "userId"

    skip: int = positive_integer_field(default=0)
    limit: int = natural_number_field(default=DEFAULT_APPOINTMENT_RESULT_PAGE_SIZE)
    requesterId: str = required_field(metadata=meta(validate_object_id))
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class DeleteAppointmentRequestObject:
    APPOINTMENT_ID = "appointmentId"
    SUBMITTER = "submitter"

    appointmentId: str = required_field(metadata=meta(validate_object_id))
    submitter: AuthorizedUser = required_field()


@convertibleclass
class BulkDeleteAppointmentsRequestObject:
    APPOINTMENT_IDS = "appointmentIds"
    SUBMITTER = "submitter"
    USER_ID = "userId"

    appointmentIds: list[str] = required_field(metadata=meta(validate_object_ids))
    submitter: AuthorizedUser = required_field()
    userId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class UpdateAppointmentRequestObject(Appointment):
    IS_USER = "isUser"
    REQUESTER_ID = "requesterId"
    BEFORE_HOURS = 3

    isUser: bool = required_field()
    requesterId: str = required_field(metadata=meta(validate_object_id))

    @classmethod
    def validate(cls, appointment):
        must_be_present(id=appointment.id)
        must_not_be_present(
            title=appointment.title,
            description=appointment.description,
            keyActionId=appointment.keyActionId,
            updateDateTime=appointment.updateDateTime,
            createDateTime=appointment.createDateTime,
            completeDateTime=appointment.completeDateTime,
        )

        if appointment.isUser:
            must_be_present(status=appointment.status)
            must_not_be_present(
                userId=appointment.userId,
                startDateTime=appointment.startDateTime,
                endDateTime=appointment.endDateTime,
                noteId=appointment.noteId,
                callId=appointment.callId,
            )
            return

        must_be_present(userId=appointment.userId)
        must_not_be_present(status=appointment.status)

        if appointment.startDateTime:
            appointment.validate_date_times()

    def post_init(self):
        if self.isUser:
            self.userId = self.requesterId
        else:
            self.managerId = self.requesterId
        self.requesterId = None
        self.updateDateTime = datetime.utcnow()

    @autoparams("repo")
    def check_permission(
        self, submitter: AuthorizedUser, repo: AuthorizationRepository
    ):
        if submitter.id == self.userId:
            return

        user = repo.retrieve_simple_user_profile(user_id=self.userId)
        authz_user = AuthorizedUser(user)
        if not are_users_in_the_same_resource(authz_user, submitter):
            raise PermissionDenied
