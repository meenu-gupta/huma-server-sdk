from datetime import datetime

from mongoengine import (
    EmbeddedDocument,
    EmbeddedDocumentField,
    ObjectIdField,
    StringField,
    ListField,
    DateTimeField,
    BooleanField,
    DictField,
)

from extensions.export_deployment.models.export_deployment_models import (
    ExportParameters,
    ExportProcess,
    ExportProfile,
)
from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoExportResultObject(EmbeddedDocument):
    bucket = StringField(required=True)
    key = StringField(required=True)


class MongoExportParams(EmbeddedDocument):
    BINARY_CHOICES = [option.value for option in ExportParameters.BinaryDataOption]
    FORMAT_CHOICES = [option.value for option in ExportParameters.DataFormatOption]
    VIEW_CHOICES = [option.value for option in ExportParameters.DataViewOption]
    LAYER_CHOICES = [option.value for option in ExportParameters.DataLayerOption]
    QUANTITY_CHOICES = [option.value for option in ExportParameters.DataQuantityOption]

    fromDate = DateTimeField()
    toDate = DateTimeField()
    moduleNames = ListField(StringField(), default=None)
    excludedModuleNames = ListField(StringField(), default=None)
    userIds = ListField(ObjectIdField(), default=None)
    deIdentified = BooleanField(default=False)
    includeNullFields = BooleanField(default=False)
    includeUserMetaData = BooleanField(default=False)
    useFlatStructure = BooleanField(default=False)
    extraQuestionIds = DictField(default=None)
    view = StringField(
        choices=VIEW_CHOICES,
        default=ExportParameters.DataViewOption.MODULE_CONFIG.value,
    )
    format = StringField(
        choices=FORMAT_CHOICES,
        default=ExportParameters.DataFormatOption.JSON.value,
    )
    binaryOption = StringField(
        choices=BINARY_CHOICES,
        default=ExportParameters.BinaryDataOption.NONE.value,
    )
    layer = StringField(
        choices=LAYER_CHOICES,
        default=ExportParameters.DataLayerOption.FLAT.value,
    )
    quantity = StringField(
        choices=QUANTITY_CHOICES,
        default=ExportParameters.DataQuantityOption.MULTIPLE.value,
    )
    questionnairePerName = BooleanField(default=False)
    splitMultipleChoice = BooleanField(default=False)
    splitSymptoms = BooleanField(default=False)
    translatePrimitives = BooleanField(default=False)
    organizationId = ObjectIdField()
    deploymentIds = ListField(ObjectIdField(), default=None)
    singleFileResponse = BooleanField(default=False)
    translationShortCodesObject = EmbeddedDocumentField(MongoS3Object)
    translationShortCodesObjectFormat = StringField(
        choices=FORMAT_CHOICES,
        default=ExportParameters.DataFormatOption.JSON.value,
    )
    includeFields = ListField(StringField())
    excludeFields = ListField(StringField())
    deIdentifyHashFields = ListField(StringField(), required=True)
    deIdentifyRemoveFields = ListField(StringField(), required=True)
    exportBucket = StringField()
    onboardingModuleNames = ListField(StringField())
    preferShortCode = BooleanField(default=False)


class MongoExportProcess(MongoPhoenixDocument):
    meta = {"collection": "exportprocess"}

    status = StringField(
        required=True,
        choices=enum_values(ExportProcess.ExportStatus),
    )
    seen = BooleanField()
    resultObject = EmbeddedDocumentField(MongoExportResultObject)

    requesterId = ObjectIdField()
    deploymentId = ObjectIdField()
    organizationId = ObjectIdField()
    deploymentIds = ListField(ObjectIdField(), default=None)
    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)
    exportParams = EmbeddedDocumentField(MongoExportParams)
    exportType = StringField(
        required=True,
        choices=enum_values(ExportProcess.ExportType),
    )
    taskId = StringField()


class MongoExportProfile(MongoPhoenixDocument):
    meta = {
        "collection": "exportprofile",
        "indexes": [
            {
                "fields": [ExportProfile.NAME, ExportProfile.DEPLOYMENT_ID],
                "unique": True,
                "partialFilterExpression": {
                    ExportProfile.DEPLOYMENT_ID: {"$exists": True}
                },
            },
            {
                "fields": [ExportProfile.NAME, ExportProfile.ORGANIZATION_ID],
                "unique": True,
                "partialFilterExpression": {
                    ExportProfile.ORGANIZATION_ID: {"$exists": True}
                },
            },
        ],
    }

    name = StringField(required=True)
    content = EmbeddedDocumentField(MongoExportParams)
    deploymentId = ObjectIdField()
    organizationId = ObjectIdField()

    updateDateTime = DateTimeField(default=datetime.utcnow)
    createDateTime = DateTimeField(default=datetime.utcnow)

    default = BooleanField()
