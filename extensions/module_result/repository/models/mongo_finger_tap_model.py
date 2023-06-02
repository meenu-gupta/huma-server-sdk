from mongoengine import IntField

from extensions.module_result.repository.models import MongoPrimitive


class MongoFingerTap(MongoPrimitive):
    meta = {"collection": "fingertap"}

    leftHandValue = IntField()
    rightHandValue = IntField()
