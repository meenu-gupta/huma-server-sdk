import logging

from flasgger import swag_from
from flask import jsonify, request, render_template, Blueprint, g
from twilio.request_validator import RequestValidator

from extensions.authorization.router.policies import get_read_policy
from extensions.common.policies import get_user_route_read_policy
from extensions.deployment.iam.iam import IAMBlueprint
from extensions.twilio_video.models.twilio_video import (
    VideoCall,
    VideoCallLog,
    VideoAction,
)
from extensions.twilio_video.router.policies import (
    test_path_policy,
    complete_call_user_policy,
    complete_call_manager_policy,
    initiate_call_policy,
)
from extensions.twilio_video.router.twilio_video_request import (
    CompleteVideoCallRequestObject,
    RetrieveCallsRequestObject,
    InitiateVideoCallRequestObject,
    CompleteUserVideoCallRequestObject,
)
from extensions.twilio_video.service.video_service import TwilioVideoService
from extensions.twilio_video.use_case.complete_video_call_public import (
    CompleteVideoCallPublicUseCase,
)
from extensions.twilio_video.use_case.retrieve_calls_usecase import (
    RetrieveVideoCallsUseCase,
)
from sdk.common.constants import SWAGGER_DIR
from sdk.common.exceptions.exceptions import PermissionDenied, DetailedException
from sdk.common.utils import inject
from sdk.common.utils.flask_request_utils import (
    get_request_json_dict_or_raise_exception,
)
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.audit_logger import audit
from sdk.phoenix.config.server_config import PhoenixServerConfig

api = IAMBlueprint(
    "video",
    __name__,
    url_prefix="/api/extensions/v1beta",
    template_folder="test_client_app/templates/",
    static_folder="test_client_app/static/",
    policy=get_user_route_read_policy,
)

public_api = Blueprint("public_video", __name__, url_prefix="/api/public/v1beta/video")

logger = logging.getLogger(__name__)


@api.route("/manager/<manager_id>/video/user/<user_id>/initiate", methods=["POST"])
@api.require_policy(initiate_call_policy)
@audit(VideoAction.InitiateVideoCall)
@swag_from(f"{SWAGGER_DIR}/initiate_video_call.yml")
def initiate_video_call(manager_id, user_id):
    appointment_id = None
    if request.json:
        appointment_id = request.json.get(
            InitiateVideoCallRequestObject.APPOINTMENT_ID, None
        )
    service = TwilioVideoService()
    room_sid, video_call_id = service.create_room(
        manager_id=manager_id, user_id=user_id, appointment_id=appointment_id
    )
    manager_token, ttl = service.generate_auth_token(
        f"manager:{manager_id}", video_call_id
    )
    return (
        jsonify(
            {
                "videoCallId": video_call_id,
                "roomSid": room_sid,
                "authToken": manager_token,
                "ttl": ttl,
            }
        ),
        201,
    )


@api.route("/manager/<manager_id>/video/<video_call_id>/complete", methods=["POST"])
@api.require_policy(complete_call_manager_policy)
@audit(VideoAction.CompleteVideoCallManager, target_key="video_call_id")
@swag_from(f"{SWAGGER_DIR}/complete_video_call_by_manager.yml")
def complete_video_call_by_manager(manager_id, video_call_id):
    service = TwilioVideoService()
    video_call = service.retrieve_video_call(video_call_id=video_call_id)
    reason = VideoCall.CallStatus.ANSWERED
    if not service.check_video_call_log_exists(
        video_call_id,
        VideoCallLog.EventType.USER_JOINED.value,
        f"user:{video_call.userId}",
    ):
        service.send_user_push_notification_call_ended(user_id=video_call.userId)
        reason = VideoCall.CallStatus.MISSED
    service.add_video_call_log(
        video_call_id,
        VideoCallLog.EventType.ROOM_FINISHED.value,
        f"manager:{manager_id}",
        reason,
    )
    service.complete_video_call(video_call_id)
    return "", 200


@api.route("/user/<user_id>/video/<video_call_id>/complete", methods=["POST"])
@api.require_policy(complete_call_user_policy)
@audit(VideoAction.CompleteVideoCallUser, target_key="video_call_id")
@swag_from(f"{SWAGGER_DIR}/complete_video_call_by_user.yml")
def complete_video_call_by_user(user_id, video_call_id):
    reason = None
    reason_key = CompleteUserVideoCallRequestObject.REASON
    if request.json and reason_key in request.json:
        request_object = CompleteUserVideoCallRequestObject.from_dict(
            {reason_key: request.json.get(reason_key)}
        )
        reason = request_object.reason
    service = TwilioVideoService()
    service.finish_video_call_for_user(video_call_id, user_id, reason)

    return "", 200


@api.route("/video/callbacks", methods=["POST"])
@api.require_policy([], override=True)
def twilio_callbacks():
    config = inject.instance(PhoenixServerConfig).server.adapters.twilioVideo
    validator = RequestValidator(config.authToken)
    request_url = request.url
    signature = request.headers.get("X-Twilio-Signature", "")

    # Validating Twilio requests
    if "https" not in request_url:
        request_url = request_url.replace("http", "https")
    request_valid = validator.validate(request_url, request.form, signature)
    if not request_valid:
        logger.warning(
            f"Twilio Request is invalid. Request Url [{request_url}], Form [{request.form}] or Signature [{signature}] is invalid"
        )
        raise PermissionDenied

    video_call_id = request.form.get("RoomName")
    room_status = request.form.get("RoomStatus")
    event = request.form.get("StatusCallbackEvent")
    duration = int(request.form.get("RoomDuration", 0))
    participant_identity = request.form.get("ParticipantIdentity")
    room_sid = request.form.get("RoomSid")
    logger.debug(f"Room {room_sid}: Callback {request.form}")

    service = TwilioVideoService()

    if event == VideoCallLog.EventType.ROOM_FINISHED.value:
        # updating duration after room closed
        video_call = VideoCall.from_dict(
            {"id": video_call_id, "roomStatus": room_status, "duration": duration},
            ignored_fields=["roomStatus"],
        )
        service.update_video_call(video_call)

    if (
        event == VideoCallLog.EventType.USER_JOINED.value
        and "manager" in participant_identity
    ):
        # send here push notification for user to join video call after manger joined the room for first time
        if not service.check_video_call_log_exists(
            video_call_id, event, participant_identity
        ):
            video_call = service.retrieve_video_call(video_call_id)
            service.send_user_push_notification_invitation(
                user_id=video_call.userId,
                room_name=video_call_id,
                manager_id=video_call.managerId,
            )

    if event == VideoCallLog.EventType.USER_LEFT.value:
        logger.info(f"Room {room_sid}: User {participant_identity} left room")
        # if everyone left room, then immediately complete it
        if len(service.retrieve_call_participants(video_call_id)) == 0:
            try:
                service.complete_video_call(room_sid)
            except DetailedException as e:
                logger.info(str(e))

    # saving only needed events
    if event in [item.value for item in VideoCallLog.EventType]:
        service.add_video_call_log(video_call_id, event, participant_identity)
    return "", 200


@api.route("/video/test", methods=["GET"])
@api.require_policy(test_path_policy, override=True)
def test_video_call():
    return render_template("video.html")


@api.route("/user/<user_id>/calls/search", methods=["GET"])
@api.require_policy(get_read_policy)
@swag_from(f"{SWAGGER_DIR}/retrieve_video_calls.yml")
def retrieve_video_calls(user_id):
    args = request.args or {}
    skip = int(args.get(RetrieveCallsRequestObject.SKIP, 0))
    limit = int(args.get(RetrieveCallsRequestObject.LIMIT, 100))
    video_call_id = args.get(RetrieveCallsRequestObject.VIDEO_CALL_ID)
    request_object = RetrieveCallsRequestObject.from_dict(
        {
            RetrieveCallsRequestObject.USER_ID: user_id,
            RetrieveCallsRequestObject.REQUESTER_ID: g.authz_user.id,
            RetrieveCallsRequestObject.SKIP: skip,
            RetrieveCallsRequestObject.LIMIT: limit,
            RetrieveCallsRequestObject.VIDEO_CALL_ID: video_call_id,
        }
    )

    response = RetrieveVideoCallsUseCase().execute(request_object)
    return jsonify(remove_none_values(response.value.to_dict())), 200


# Public routes


@public_api.route("/<video_call_id>/complete", methods=["POST"])
@audit(VideoAction.CompleteVideoCallUser, target_key="video_call_id")
@swag_from(f"{SWAGGER_DIR}/complete_video_call_public.yml")
def complete_video_call_public(video_call_id):
    body = get_request_json_dict_or_raise_exception(request)
    body.update({CompleteVideoCallRequestObject.CALL_ID: video_call_id})
    request_object = CompleteVideoCallRequestObject.from_dict(body)
    CompleteVideoCallPublicUseCase().execute(request_object)
    return "", 200
