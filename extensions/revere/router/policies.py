import logging

from flask import request, g

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.common.policies import is_self_request, get_user_route_write_policy
from extensions.revere.models.revere import RevereTest
from sdk.common.exceptions.exceptions import PermissionDenied

logger = logging.getLogger(__file__)


def get_read_revere_tests_policy():
    """ To not allow owner retrieve list of not finished tests. """
    authz_user: AuthorizedUser = g.authz_user
    body = request.json or {}
    status = body.get(RevereTest.STATUS)
    if is_self_request() and status != RevereTest.Status.FINISHED.value:
        msg = f"%s #[%s] can not retrieve list of not finished test."
        logger.warning(msg % (authz_user.get_role().id, authz_user.id))
        raise PermissionDenied


def get_write_revere_tests_policy():
    """ To not allow owner retrieve list of not finished tests. """
    if not is_self_request():
        raise PermissionDenied
    return get_user_route_write_policy()
