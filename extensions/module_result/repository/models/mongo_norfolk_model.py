from mongoengine import FloatField
from extensions.module_result.repository.models import MongoPrimitive


class MongoNORFOLK(MongoPrimitive):
    meta = {"collection": "norfolk"}

    totalQolScore = FloatField()
    physicalFunctionLargeFiber = FloatField()
    activitiesOfDailyLiving = FloatField()
    symptoms = FloatField()
    smallFiber = FloatField()
    automic = FloatField()
