import logging
import typing

import mohawk
from flask import request
from mohawk.exc import (
    MacMismatch,
    AlreadyProcessed,
    TokenExpired,
    MisComputedContentHash,
    BadHeaderValue,
    HawkFail,
)
from redis import Redis

from sdk import convertibleclass
from sdk.auth.model.auth_user import AuthKey
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.exceptions.exceptions import PermissionDenied, InvalidRequestException
from sdk.common.utils import inject
from sdk.common.utils.convertible import default_field
from sdk.common.utils.token.hawk.exceptions import (
    HawkRequestAlreadyProcessed,
    HawkMacMismatch,
    HawkTokenExpired,
    HawkMisComputedContentHash,
    HawkInvalidUserKey,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig

log = logging.getLogger(__name__)


@convertibleclass
class UserKey:
    USER_ID = "userId"
    AUTH_IDENTIFIER = "authIdentifier"

    userId: str = default_field()
    authIdentifier: str = default_field()

    @classmethod
    def from_string(cls, user_key: str):
        if "." not in user_key or len(user_key.split(".")) != 2:
            raise HawkInvalidUserKey

        user_id, auth_id = user_key.split(".")
        return cls.from_dict({cls.USER_ID: user_id, cls.AUTH_IDENTIFIER: auth_id})

    def __str__(self):
        return f"{self.userId}.{self.authIdentifier}"

    def to_string(self):
        return str(self)


def lookup_user_factory(hashing_algorithm: str) -> typing.Callable[[str], dict]:
    def lookup_user(compound_user_key: str) -> dict:
        user_key = UserKey.from_string(compound_user_key)
        auth_repo = inject.instance(AuthRepository)
        auth_key = auth_repo.retrieve_auth_key(
            user_id=user_key.userId, auth_identifier=user_key.authIdentifier
        )
        return {
            "id": user_key.userId,
            "key": auth_key[AuthKey.AUTH_KEY],
            "algorithm": hashing_algorithm,
        }

    return lookup_user


def seen_nonce_factory(timestamp_skew: int):
    def seen_nonce(user_key: str, nonce: str, timestamp: int) -> bool:
        redis = inject.instance(Redis)
        key = f"hawk:{user_key}:{nonce}:{timestamp}"
        if redis.get(key):
            return True
        else:
            redis.set(key, 1, ex=timestamp_skew)
            return False

    return seen_nonce


def get_hawk_receiver(header_name: str = "Authorization") -> mohawk.Receiver:
    server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    authorization_header = request.headers.get(header_name, None)
    if not server_config.server.adapters.hawk:
        log.warning("Please configure hawk in the config file")
        raise PermissionDenied
    hashing_algorithm = server_config.server.adapters.hawk.hashingAlgorithm
    time_stamp_skew = server_config.server.adapters.hawk.timeStampSkew
    local_time_offset = server_config.server.adapters.hawk.localTimeOffset
    try:
        receiver = mohawk.Receiver(
            credentials_map=lookup_user_factory(hashing_algorithm=hashing_algorithm),
            request_header=authorization_header,
            url=request.url,
            method=request.method,
            content=request.get_data(),
            content_type=request.mimetype,
            accept_untrusted_content=False,
            timestamp_skew_in_seconds=time_stamp_skew,
            localtime_offset_in_seconds=local_time_offset,
            seen_nonce=seen_nonce_factory(time_stamp_skew),
        )
    except (
        AlreadyProcessed,
        MacMismatch,
        TokenExpired,
        MisComputedContentHash,
    ) as exception:
        exceptions_map = {
            AlreadyProcessed: HawkRequestAlreadyProcessed,
            MacMismatch: HawkMacMismatch,
            TokenExpired: HawkTokenExpired,
            MisComputedContentHash: HawkMisComputedContentHash,
        }
        raise exceptions_map[exception.__class__]
    except (BadHeaderValue, HawkFail):
        raise InvalidRequestException("Couldn't parse Hawk header")
    else:
        return receiver
