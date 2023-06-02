import logging

from flasgger import swag_from
from flask import Blueprint, request, jsonify, g

from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
    prepare_and_send_push_notification_for_voip_user,
)
from sdk.auth.model.auth_user import AuthUser
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils.flask_request_utils import (
    validate_request_body_type_is_object,
)
from sdk.notification.model.device import Device
from sdk.notification.router.notification_requests import (
    RegisterDeviceRequestObject,
    UnRegisterDeviceRequestObject,
)
from sdk.notification.services.notification_service import NotificationService

api = Blueprint("notification_route", __name__, url_prefix="/api/notification/v1beta")
logger = logging.getLogger(__name__)


@api.route("/device/register", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/register_device_swag.yml")
def register_device():
    body = validate_request_body_type_is_object(request)

    user: AuthUser = g.auth_user

    body[Device.USER_ID] = user.id
    device = RegisterDeviceRequestObject.from_dict(body)

    svc = NotificationService()
    inserted_id = svc.register_device(device)

    return jsonify({"id": inserted_id}), 201


@api.route("/device/unregister", methods=["DELETE"])
@swag_from(f"{SWAGGER_DIR}/unregister_device_swag.yml")
def unregister_device():
    body = validate_request_body_type_is_object(request)

    user: AuthUser = g.auth_user
    body["userId"] = user.id

    req_object = UnRegisterDeviceRequestObject.from_dict(body)

    svc = NotificationService()
    svc.unregister_device(
        user_id=req_object.userId, device_push_id=req_object.devicePushId
    )

    return "", 204


@api.route("/device", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_devices_swag.yml")
def get_user_devices():
    user: AuthUser = g.auth_user

    svc = NotificationService()
    devices = svc.retrieve_devices(user.id)

    devices_dict_list = [device.to_dict() for device in devices]
    response = {"items": devices_dict_list, "total": len(devices_dict_list)}
    return jsonify(response), 200


@api.route("/push", methods=["POST"])
def send_notification():
    """
    FOR TESTING PURPOSES
    """

    body_ = validate_request_body_type_is_object(request)
    title = body_["title"]
    body = body_["body"]
    user_id = body_["userId"]
    action = "Test Notification"
    notification_template = {"title": title, "body": body}
    prepare_and_send_push_notification(user_id, action, notification_template)

    return jsonify({}), 200


@api.route("/push/voip", methods=["POST"])
def send_notification_call():
    """
    FOR TESTING PURPOSES
    """

    body_ = validate_request_body_type_is_object(request)
    title = body_["title"]
    body = body_["body"]
    user_id = body_["userId"]
    action = "Test VOIP Notification"
    notification_template = {"title": title, "body": body}
    prepare_and_send_push_notification_for_voip_user(
        user_id, action, notification_template
    )

    return jsonify({}), 200
