from mongoengine import FloatField

from extensions.module_result.repository.models import MongoPrimitive


class MongoLysholm(MongoPrimitive):
    meta = {"collection": "lysholm"}

    limp = FloatField()
    caneOrCrutches = FloatField()
    lockingSensation = FloatField()
    givingWaySensation = FloatField()
    pain = FloatField()
    swelling = FloatField()
    climbingStairs = FloatField()
    squatting = FloatField()
    lysholm = FloatField()
