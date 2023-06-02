from mongoengine import (
    StringField,
    BooleanField,
    DateTimeField,
    EmbeddedDocumentField,
    ListField,
    ObjectIdField,
)

from extensions.deployment.models.deployment import TemplateCategory
from extensions.deployment.models.status import EnableStatus
from extensions.deployment.repository.models.mongo_deployment_model import (
    MongoEmbeddedDeployment,
)
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoDeploymentTemplateModel(MongoPhoenixDocument):
    meta = {"collection": "deploymenttemplate"}

    name = StringField()
    description = StringField()
    organizationIds = ListField(ObjectIdField())
    category = StringField(choices=enum_values(TemplateCategory))
    template = EmbeddedDocumentField(MongoEmbeddedDeployment)
    status = StringField(choices=enum_values(EnableStatus))
    isVerified = BooleanField()
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
