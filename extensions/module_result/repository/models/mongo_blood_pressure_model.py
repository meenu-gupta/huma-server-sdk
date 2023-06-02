from mongoengine import IntField, StringField

from extensions.module_result.models.primitives.primitive import HumaMeasureUnit
from extensions.module_result.repository.models import MongoPrimitive
from sdk.common.utils.enum_utils import enum_values


class MongoBloodPressure(MongoPrimitive):
    meta = {"collection": "bloodpressure"}

    diastolicValue = IntField()
    systolicValue = IntField()
    unitSi = StringField()
    diastolicValueUnit = StringField(choices=enum_values(HumaMeasureUnit))
    systolicValueUnit = StringField(choices=enum_values(HumaMeasureUnit))
