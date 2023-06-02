from mongoengine import (
    ObjectIdField,
    DateTimeField,
    StringField,
    BooleanField,
    FloatField,
    DictField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    EmbeddedDocument,
)

from extensions.medication.models.medication import MedicationHistory
from extensions.medication.repository.models.mongo_medications_schedule_model import (
    MongoMedicationSchedule,
)
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoMedicationBase(EmbeddedDocument):
    id = ObjectIdField()
    prn = BooleanField()
    enabled = BooleanField()
    userId = ObjectIdField()
    deploymentId = ObjectIdField()
    moduleId = StringField()
    name = StringField()
    doseQuantity = FloatField()
    doseUnits = StringField()
    schedule = EmbeddedDocumentField(MongoMedicationSchedule)
    extraProperties = DictField(default=None)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()


class MongoMedicationHistory(MongoMedicationBase):
    changeType = StringField(choices=enum_values(MedicationHistory.ChangeType))


class MongoMedication(MongoPhoenixDocument, MongoMedicationBase):
    meta = {"collection": "Medication"}
    changeHistory = EmbeddedDocumentListField(MongoMedicationHistory)
