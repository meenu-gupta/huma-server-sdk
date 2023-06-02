from mongoengine import FloatField, StringField

from extensions.module_result.models.primitives.primitive import HumaMeasureUnit
from extensions.module_result.repository.models import MongoPrimitive
from sdk.common.utils.enum_utils import enum_values


class MongoBodyMeasurement(MongoPrimitive):
    meta = {"collection": "bodymeasurement"}

    visceralFat = FloatField()
    totalBodyFat = FloatField()
    waistCircumference = FloatField()
    waistCircumferenceUnit = StringField(choices=enum_values(HumaMeasureUnit))
    hipCircumference = FloatField()
    hipCircumferenceUnit = StringField(choices=enum_values(HumaMeasureUnit))
    waistToHipRatio = FloatField()
