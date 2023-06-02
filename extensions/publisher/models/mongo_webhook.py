from mongoengine import StringField, URLField, EmbeddedDocument

from extensions.publisher.models.webhook import Webhook
from sdk.common.utils.enum_utils import enum_values


class MongoWebhook(EmbeddedDocument):
    endpoint = URLField()
    authType = StringField(
        choices=enum_values(Webhook.WebhookAuthType),
        default=Webhook.WebhookAuthType.NONE.value,
    )
    username = StringField()
    password = StringField()
    token = StringField()
