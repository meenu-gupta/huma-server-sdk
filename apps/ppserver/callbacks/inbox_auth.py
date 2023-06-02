from flask import g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.common.policies import get_user_route_policy
from extensions.deployment.iam.iam import IAMBlueprint
from sdk.common.exceptions.exceptions import PermissionDenied
from sdk.inbox.events.auth_events import InboxSearchAuthEvent, InboxSendAuthEvent


def setup_inbox_send_auth(_: InboxSendAuthEvent):
    policy = get_user_route_policy(None, PolicyType.SEND_PATIENT_MESSAGE)
    if policy is None:
        raise PermissionDenied
    IAMBlueprint.check_permissions([policy])
    g.user_full_name = g.user.get_full_name()


def setup_inbox_search_auth(_: InboxSearchAuthEvent):
    policy = get_user_route_policy(
        PolicyType.VIEW_OWN_MESSAGES, PolicyType.VIEW_PATIENT_MESSAGE
    )
    IAMBlueprint.check_permissions([policy])


def setup_inbox_confirm_auth(_: InboxSearchAuthEvent):
    policy = get_user_route_policy(PolicyType.VIEW_OWN_MESSAGES, None)
    if policy is None:
        raise PermissionDenied
    IAMBlueprint.check_permissions([policy])
