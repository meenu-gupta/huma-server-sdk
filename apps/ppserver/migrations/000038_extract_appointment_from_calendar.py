from datetime import timedelta

import isodate

from extensions.appointment.models.appointment import Appointment
from extensions.appointment.models.mongo_appointment import MongoAppointment
from sdk.calendar.models.calendar_event import CalendarEvent as Event
from sdk.common.mongodb_migrations.base import BaseMigration
from sdk.common.utils.validators import remove_none_values

calendar_collection_name = "calendar"
appointment_collection_name = "appointment"


class Migration(BaseMigration):
    def upgrade(self):
        calendar_collection = self.db.get_collection(calendar_collection_name)
        if not calendar_collection:
            return
        query = {Event.MODEL: Appointment.__name__, Event.ENABLED: True}
        results = calendar_collection.find(query)
        appointments = [calendar_event_to_appointment(event) for event in results]
        if not appointments:
            return

        self.save_appointments(appointments)
        calendar_collection.delete_many(query)

    def downgrade(self):
        pass

    def save_appointments(self, appointments: list[dict]):
        appointment_collection = self.db.get_collection(appointment_collection_name)
        if appointment_collection is None:
            self.db.create_collection(appointment_collection_name)
            appointment_collection = self.db.get_collection(appointment_collection_name)
        appointment_collection.insert_many(appointments)


def calendar_event_to_appointment(event: dict):
    extra_fields = event.get(Event.EXTRA_FIELDS) or {}
    start = event.get(Event.START_DATE_TIME)
    end = event.get(Event.END_DATE_TIME)
    delta = event.get(Event.INSTANCE_EXPIRES_IN)
    delta = isodate.parse_duration(delta) if delta else None
    if delta and start != end and (end - start) > timedelta(hours=2):
        new_start = start + delta
        if new_start > end:
            start = end
        else:
            start = new_start
    appointment = {
        "_cls": MongoAppointment.__name__,
        Appointment.TITLE: event.get(Event.TITLE),
        Appointment.DESCRIPTION: event.get(Event.DESCRIPTION),
        Appointment.USER_ID: event.get(Event.USER_ID),
        Appointment.MANAGER_ID: extra_fields.get(Appointment.MANAGER_ID),
        Appointment.STATUS: extra_fields.get(Appointment.STATUS),
        Appointment.NOTE_ID: extra_fields.get(Appointment.NOTE_ID),
        Appointment.CALL_ID: extra_fields.get(Appointment.CALL_ID),
        Appointment.START_DATE_TIME: start,
        Appointment.END_DATE_TIME: end,
        Appointment.UPDATE_DATE_TIME: event.get(Event.UPDATE_DATE_TIME),
        Appointment.CREATE_DATE_TIME: event.get(Event.CREATE_DATE_TIME),
    }
    return remove_none_values(appointment)
