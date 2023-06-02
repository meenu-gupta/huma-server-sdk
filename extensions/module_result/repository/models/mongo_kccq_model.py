from mongoengine import FloatField
from extensions.module_result.repository.models import MongoPrimitive


class MongoKCCQ(MongoPrimitive):
    meta = {"collection": "kccq"}

    physicalLimitation = FloatField()
    symptomStability = FloatField()
    symptomFrequency = FloatField()
    symptomBurden = FloatField()
    totalSymptomScore = FloatField()
    selfEfficacy = FloatField()
    qualityOfLife = FloatField()
    socialLimitation = FloatField()
    overallSummaryScore = FloatField()
    clinicalSummaryScore = FloatField()
