from mongoengine import (
    StringField,
    FloatField,
    IntField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)

from extensions.module_result.models.primitives.primitive import HumaMeasureUnit
from extensions.module_result.models.primitives.primitive_heart_rate import HeartRate
from extensions.module_result.repository.models import MongoPrimitive
from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.enum_utils import enum_values
from .mongo_questionnaire_model import MongoQuestionnaireAnswer


class QuestionnaireMetadata(EmbeddedDocument):
    answers = EmbeddedDocumentListField(MongoQuestionnaireAnswer)


class MongoHeartRate(MongoPrimitive):
    meta = {"collection": "heartrate"}

    value = IntField()
    heartRateType = StringField(choices=enum_values(HeartRate.HeartRateType))

    classification = StringField()
    source = StringField()

    variabilityAVNN = IntField()
    variabilitySDNN = IntField()
    variabilityRMSSD = IntField()
    variabilityPNN50 = FloatField()
    variabilityprcLF = FloatField()
    confidence = IntField()
    goodIBI = IntField()
    rawDataObject = EmbeddedDocumentField(MongoS3Object)
    valueUnit = StringField(choices=enum_values(HumaMeasureUnit))

    metadata = EmbeddedDocumentField(QuestionnaireMetadata)
