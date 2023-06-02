from mongoengine import FloatField, StringField

from extensions.module_result.models.primitives.primitive import HumaMeasureUnit
from extensions.module_result.repository.models import MongoPrimitive
from sdk.common.utils.enum_utils import enum_values


class MongoHeight(MongoPrimitive):
    meta = {"collection": "height"}

    value = FloatField()
    valueUnit = StringField(choices=enum_values(HumaMeasureUnit))
