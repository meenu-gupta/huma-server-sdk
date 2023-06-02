from mongoengine import ObjectIdField, StringField, IntField, EmbeddedDocument

from extensions.medication.models.medication_schedule import MedicationSchedule
from sdk.common.utils.enum_utils import enum_values


class MongoMedicationSchedule(EmbeddedDocument):
    id = ObjectIdField()
    frequency = IntField()
    period = IntField()
    periodUnit = StringField(choices=enum_values(MedicationSchedule.PeriodUnit))
