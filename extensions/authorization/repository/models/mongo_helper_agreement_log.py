from mongoengine import ObjectIdField, DateTimeField, StringField

from extensions.authorization.models.helper_agreement_log import HelperAgreementLog
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoHelperAgreementLog(MongoPhoenixDocument):
    meta = {"collection": "helperagreementlog"}

    id = ObjectIdField()
    userId = ObjectIdField()
    deploymentId = ObjectIdField()
    status = StringField(choices=enum_values(HelperAgreementLog.Status))
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
