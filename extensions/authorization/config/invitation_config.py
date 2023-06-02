from dataclasses import field

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import default_field
from sdk.phoenix.config.server_config import BasePhoenixConfig


def _required():
    return meta(required=True)


@convertibleclass
class InvitationConfig(BasePhoenixConfig):
    invitationExpiresAfterMinutes: int = default_field()
    maxInvitationResendTimes: int = field(default=5)
    shortenedCodeLength: int = field(default=16)
