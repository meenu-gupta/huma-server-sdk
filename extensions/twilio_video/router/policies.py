from flask import request, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.router.policies import manager_user_in_the_same_resource
from extensions.twilio_video.service.video_service import TwilioVideoService
from sdk.common.decorator.debug_route import debug_route
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.common.utils.inject import autoparams


@debug_route(PermissionDenied)
def test_path_policy():
    return


@autoparams("repo")
def initiate_call_policy():
    manager_id = request.view_args.get("manager_id")
    user_id = request.view_args.get("user_id")

    if not (manager_id or user_id):
        raise PermissionDenied

    if manager_id != g.authz_user.id:
        raise PermissionDenied

    return manager_user_in_the_same_resource(
        user_id, PolicyType.SCHEDULE_AND_CALL_PATIENT
    )


def complete_call_manager_policy():
    video_call_id = request.view_args.get("video_call_id")
    path_manager_id = request.view_args.get("manager_id")

    service = TwilioVideoService()
    video_call = service.retrieve_video_call(video_call_id=video_call_id)

    if path_manager_id and path_manager_id != video_call.managerId:
        raise PermissionDenied


def complete_call_user_policy():
    video_call_id = request.view_args.get("video_call_id")
    path_user_id = request.view_args.get("user_id")
    service = TwilioVideoService()
    video_call = service.retrieve_video_call(video_call_id=video_call_id)

    if path_user_id and path_user_id != video_call.userId:
        raise PermissionDenied
