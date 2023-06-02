from extensions.publisher.models.publisher import Publisher
from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    positive_integer_field,
    natural_number_field,
)
from sdk.common.utils.validators import (
    must_be_present,
    must_not_be_present,
    validate_object_id,
)


@convertibleclass
class CreatePublisherRequestObject(Publisher):
    @classmethod
    def validate(cls, publisher):
        if (
            publisher.filter.listenerType
            == Publisher.Filter.ListenerType.DEPLOYMENT_IDS
        ):
            must_be_present(deploymentIds=publisher.filter.deploymentIds)
        if (
            publisher.filter.listenerType
            == Publisher.Filter.ListenerType.ORGANIZATION_IDS
        ):
            must_be_present(organizationIds=publisher.filter.organizationIds)
        if publisher.target.publisherType == Publisher.Target.Type.KAFKA:
            must_be_present(kafka=publisher.target.kafka)
        if publisher.target.publisherType == Publisher.Target.Type.WEBHOOK:
            must_be_present(webhook=publisher.target.webhook)
        if publisher.target.publisherType == Publisher.Target.Type.GCPFHIR:
            must_be_present(gcp_fhir=publisher.target.gcp_fhir)

        must_not_be_present(
            id=publisher.id,
            updateDateTime=publisher.updateDateTime,
            createDateTime=publisher.createDateTime,
        )


@convertibleclass
class UpdatePublisherRequestObject(Publisher):
    @classmethod
    def validate(cls, publisher):
        must_be_present(id=publisher.id)

        if (
            publisher.filter.listenerType
            == Publisher.Filter.ListenerType.DEPLOYMENT_IDS
        ):
            must_be_present(deploymentIds=publisher.filter.deploymentIds)
        if (
            publisher.filter.listenerType
            == Publisher.Filter.ListenerType.ORGANIZATION_IDS
        ):
            must_be_present(organizationIds=publisher.filter.organizationIds)
        if publisher.target.publisherType == Publisher.Target.Type.KAFKA:
            must_be_present(kafka=publisher.target.kafka)
        if publisher.target.publisherType == Publisher.Target.Type.WEBHOOK:
            must_be_present(kafka=publisher.target.webhook)

        must_not_be_present(
            updateDateTime=publisher.updateDateTime,
            createDateTime=publisher.createDateTime,
        )


@convertibleclass
class RetrievePublisherRequestObject(RequestObject):
    publisherId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrievePublishersRequestObject(RequestObject):
    SKIP = "skip"
    LIMIT = "limit"

    skip: int = positive_integer_field(default=None, metadata=meta(required=True))
    limit: int = natural_number_field(default=None, metadata=meta(required=True))


@convertibleclass
class DeletePublisherRequestObject(RequestObject):
    publisherId: str = required_field(metadata=meta(validate_object_id))
