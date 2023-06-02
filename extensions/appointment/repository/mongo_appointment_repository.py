from datetime import datetime

from bson import ObjectId
from pymongo.database import Database
from pymongo import MongoClient, WriteConcern

from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.mongo_appointment import MongoAppointment
from extensions.appointment.repository.appointment_repository import (
    AppointmentRepository,
)
from sdk.common.exceptions.exceptions import ObjectDoesNotExist
from sdk.common.utils.inject import autoparams
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoAppointmentRepository(AppointmentRepository):
    APPOINTMENT_COLLECTION = "appointment"

    @autoparams()
    def __init__(self, database: Database, client: MongoClient):
        self._db = database
        self._client = client

    def create_appointment(self, appointment: Appointment) -> str:
        new_appointment: MongoPhoenixDocument = MongoAppointment(
            **appointment.to_dict(include_none=False)
        )
        return str(new_appointment.save().id)

    def unset_key_action(self, appointment_id: str) -> Appointment:
        appointment = MongoAppointment.objects(id=appointment_id).first()
        if not appointment:
            raise ObjectDoesNotExist
        appointment.keyActionId = None
        appointment.save()
        return Appointment.from_dict(appointment.to_dict())

    def update_appointment(
        self, appointment_id: str, appointment: Appointment
    ) -> Appointment:
        old_appointment = MongoAppointment.objects(id=appointment_id).first()
        if not old_appointment:
            raise ObjectDoesNotExist
        data = appointment.to_dict(include_none=False)
        old_appointment.update(**data)
        return Appointment.from_dict({**old_appointment.to_dict(), **data})

    def retrieve_appointment(self, appointment_id: str) -> Appointment:
        appointment = MongoAppointment.objects(id=appointment_id).first()
        if not appointment:
            raise ObjectDoesNotExist
        return Appointment.from_dict(appointment.to_dict())

    def retrieve_appointments_by_ids(
        self, appointment_ids: list[str]
    ) -> list[Appointment]:
        results = MongoAppointment.objects(id__in=appointment_ids)
        appointments = [Appointment.from_dict(result.to_dict()) for result in results]
        return appointments

    def retrieve_appointments(
        self,
        user_id: str,
        requester_id: str,
        from_date_time: datetime = None,
        to_date_time: datetime = None,
        status: Appointment.Status = None,
        skip: int = None,
        limit: int = None,
    ) -> list[Appointment]:
        options = {Appointment.USER_ID: user_id}

        if requester_id != user_id:
            options.update({Appointment.MANAGER_ID: requester_id})

        if from_date_time:
            options.update({f"{Appointment.START_DATE_TIME}__gte": from_date_time})

        if to_date_time:
            options.update({f"{Appointment.START_DATE_TIME}__lte": to_date_time})

        if status:
            options.update({Appointment.STATUS: status.value})

        results = MongoAppointment.objects(**options).order_by("-startDateTime")
        if skip:
            results = results.skip(skip)
        if limit:
            results = results.limit(limit)

        return [Appointment.from_dict(a.to_dict()) for a in results]

    def retrieve_pending_appointment_count(self, user_id: str) -> int:
        query = {
            Appointment.USER_ID: user_id,
            f"{Appointment.START_DATE_TIME}__gte": datetime.utcnow(),
            Appointment.STATUS: Appointment.Status.PENDING_CONFIRMATION.value,
        }

        return MongoAppointment.objects(**query).count()

    def delete_appointment(self, appointment_id: str):
        deleted = MongoAppointment.objects(id=appointment_id).delete()
        if not deleted:
            raise ObjectDoesNotExist

    def bulk_delete_appointments(self, appointment_ids: list[str]) -> int:
        appointment_ids_count = len(set(appointment_ids))
        query = {
            "_id": {
                "$in": [ObjectId(appointment_id) for appointment_id in appointment_ids]
            }
        }
        with self._client.start_session() as session:
            with session.start_transaction(
                write_concern=WriteConcern("majority", wtimeout=10000),
            ):
                result = self._db[self.APPOINTMENT_COLLECTION].delete_many(
                    query, session=session
                )
                if result.deleted_count != appointment_ids_count:
                    raise ObjectDoesNotExist
        return appointment_ids_count
