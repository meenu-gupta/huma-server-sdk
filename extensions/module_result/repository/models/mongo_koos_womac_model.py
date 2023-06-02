from mongoengine import FloatField
from extensions.module_result.repository.models import MongoPrimitive


class MongoWOMAC(MongoPrimitive):
    meta = {"collection": "womac"}

    painScore = FloatField()
    symptomsScore = FloatField()
    adlScore = FloatField()
    totalScore = FloatField()


class MongoKOOS(MongoPrimitive):
    meta = {"collection": "koos"}

    adlScore = FloatField()
    qualityOfLifeScore = FloatField()
    painScore = FloatField()
    symptomsScore = FloatField()
    sportRecreationScore = FloatField()
