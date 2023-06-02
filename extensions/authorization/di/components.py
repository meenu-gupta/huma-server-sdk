import logging

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.adapters.user_email_adapter import UserEmailAdapter
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.authorization.repository.invitation_repository import (
    InvitationRepository,
)
from extensions.authorization.repository.mongo_auth_repository import (
    MongoAuthorizationRepository,
)
from extensions.authorization.repository.mongo_invitation_repository import (
    MongoInvitationRepository,
)
from sdk.common.adapter.event_bus_adapter import BaseEvent

logger = logging.getLogger("authorization")


class PostCreateUserEvent(BaseEvent):
    user: User = None

    def __init__(self, user: User):
        self.user = user


def bind_authorization_repository(binder):
    binder.bind_to_provider(
        AuthorizationRepository, lambda: MongoAuthorizationRepository()
    )
    logger.debug("Bind AuthorizationRepository to Mongo Authorization Repository")


def bind_invitation_repository(binder):
    binder.bind_to_provider(InvitationRepository, lambda: MongoInvitationRepository())

    logger.debug(f"InvitationRepository bind to MongoInvitationRepository")


def bind_email_invitation_adapter(binder):
    binder.bind_to_provider(EmailInvitationAdapter, lambda: EmailInvitationAdapter())

    logger.debug(f"EmailInvitationAdapter bind")


def bind_user_email_adapter(binder):
    binder.bind_to_provider(UserEmailAdapter, lambda: UserEmailAdapter())

    logger.debug("UserEmailAdapter bind")


def bind_default_roles(binder):
    binder.bind(DefaultRoles, DefaultRoles())
    logger.debug(f"Default Roles bind to Default roles")
