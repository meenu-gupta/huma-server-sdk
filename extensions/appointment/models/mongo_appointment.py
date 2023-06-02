from mongoengine import ObjectIdField, StringField, DateTimeField

from extensions.appointment.models.appointment import Appointment
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoAppointment(MongoPhoenixDocument):
    meta = {
        "collection": "appointment",
        "indexes": [
            ("userId", "status", "startDateTime"),
        ],
    }

    userId = ObjectIdField()
    title = StringField()
    description = StringField()
    managerId = ObjectIdField()
    status = StringField(choices=enum_values(Appointment.Status))
    noteId = ObjectIdField()
    callId = ObjectIdField()
    keyActionId = ObjectIdField(default=None)
    startDateTime = DateTimeField()
    endDateTime = DateTimeField()
    completeDateTime = DateTimeField()
    createDateTime = DateTimeField()
    updateDateTime = DateTimeField()
