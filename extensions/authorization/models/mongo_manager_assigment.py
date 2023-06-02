from datetime import datetime

from mongoengine import ObjectIdField, DateTimeField, ListField

from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoManagerAssignment(MongoPhoenixDocument):
    PATIENT_MANAGER_ASSIGNMENT_COLLECTION = "patientmanagerassignment"
    PATIENT_MANAGER_ASSIGNMENT_LOG_COLLECTION = "patientmanagerassignmentlog"
    USER_ID = "userId"
    MANAGERS_ID = "managerIds"
    SUBMITTER_ID = "submitterId"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    meta = {"collection": PATIENT_MANAGER_ASSIGNMENT_COLLECTION}

    userId = ObjectIdField(required=True)
    managerIds = ListField(ObjectIdField(required=True))
    submitterId = ObjectIdField(required=True)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField(default=datetime.utcnow)
