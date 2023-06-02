from flasgger import swag_from
from flask import request, jsonify

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.publisher.models.publisher import Publisher, PublisherAction
from extensions.publisher.router.publisher_requests import (
    CreatePublisherRequestObject,
    UpdatePublisherRequestObject,
    RetrievePublishersRequestObject,
    DeletePublisherRequestObject,
    RetrievePublisherRequestObject,
)
from extensions.publisher.use_case.publisher_use_case import (
    UpdatePublisherUseCase,
    CreatePublisherUseCase,
    RetrievePublisherUseCase,
    RetrievePublishersUseCase,
    DeletePublisherUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit

publisher_route = IAMBlueprint(
    "publisher_route",
    __name__,
    url_prefix="/api/extensions/v1beta/publisher",
    policy=PolicyType.PUBLISH_PATIENT_DATA,
)


@publisher_route.route("", methods=["POST"])
@audit(PublisherAction.CreatePublisher)
@swag_from(f"{SWAGGER_DIR}/create_publisher.yml")
def create_publisher():
    body = get_request_json_dict_or_raise_exception(request)

    request_object = CreatePublisherRequestObject.from_dict(remove_none_values(body))

    response = CreatePublisherUseCase().execute(request_object)
    return jsonify({"id": response.value}), 201


@publisher_route.route("/<publisher_id>", methods=["PUT"])
@audit(PublisherAction.UpdatePublisher, target_key="publisher_id")
@swag_from(f"{SWAGGER_DIR}/update_publisher.yml")
def update_publisher(publisher_id):
    body = get_request_json_dict_or_raise_exception(request)

    request_object = UpdatePublisherRequestObject.from_dict(
        {Publisher.ID: publisher_id, **remove_none_values(body)}
    )
    response = UpdatePublisherUseCase().execute(request_object)
    return jsonify({"id": response.value}), 200


@publisher_route.route("/search", methods=["POST"])
@audit(PublisherAction.RetrievePublishers)
@swag_from(f"{SWAGGER_DIR}/retrieve_publishers.yml")
def retrieve_publishers():
    body = get_request_json_dict_or_raise_exception(request)
    request_object: RetrievePublishersRequestObject = (
        RetrievePublishersRequestObject.from_dict(body)
    )

    response = RetrievePublishersUseCase().execute(request_object)

    return jsonify(response.value), 200


@publisher_route.route("/<publisher_id>", methods=["DELETE"])
@audit(PublisherAction.DeletePublisher, target_key="publisher_id")
@swag_from(f"{SWAGGER_DIR}/delete_publisher.yml")
def delete_publisher(publisher_id):
    request_object = DeletePublisherRequestObject.from_dict(
        {"publisherId": publisher_id}
    )
    DeletePublisherUseCase().execute(request_object)

    return "", 204


@publisher_route.route("/<publisher_id>", methods=["GET"])
@audit(PublisherAction.RetrievePublisher, target_key="publisher_id")
@swag_from(f"{SWAGGER_DIR}/retrieve_publisher.yml")
def retrieve_publisher(publisher_id):
    request_object = RetrievePublisherRequestObject.from_dict(
        {"publisherId": publisher_id}
    )

    response = RetrievePublisherUseCase().execute(request_object)

    return jsonify(response.value.to_dict()), 200
