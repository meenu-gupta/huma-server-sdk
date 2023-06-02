from flask import g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.common.policies import (
    is_self_request,
    submitter_and_target_have_same_resource,
)
from sdk.common.exceptions.exceptions import PermissionDenied


def get_write_events_policy():
    policy = PolicyType.EDIT_OWN_EVENTS
    submitter: AuthorizedUser = g.authz_user
    target_user: AuthorizedUser = g.authz_path_user
    if not target_user or submitter.is_proxy_for_user(target_user.id):
        return policy

    if not is_self_request():
        if not submitter_and_target_have_same_resource():
            raise PermissionDenied
        policy = PolicyType.EDIT_PATIENT_EVENTS
    return policy
