from mongoengine import FloatField

from extensions.module_result.repository.models import MongoPrimitive


class MongoTegner(MongoPrimitive):
    meta = {"collection": "tegner"}

    activityLevelBefore = FloatField()
    activityLevelCurrent = FloatField()
