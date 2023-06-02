from typing import Optional

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from sdk.common.adapter.event_bus_adapter import BaseEvent


class PostUserAddRoleEvent(BaseEvent):
    def __init__(
        self,
        submitter: AuthorizedUser,
        user: User,
        new_role: str,
        old_role: Optional[str],
        resource_name: Optional[str],
    ):
        self.submitter = submitter
        self.user = AuthorizedUser(user)
        self.new_role = new_role
        self.old_role = old_role
        self.resource_name = resource_name
