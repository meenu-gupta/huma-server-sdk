from enum import Enum

from sdk.common.exceptions.exceptions import DetailedException


class ErrorCodes(Enum):
    HAWK_REQUEST_ALREADY_PROCESSED = 130001
    HAWK_MAC_MISMATCH = 130002
    HAWK_TOKEN_EXPIRED = 130003
    HAWK_MIS_COMPUTED_CONTENT_HASH = 130004
    HAWK_INVALID_USER_KEY = 130005


class HawkRequestAlreadyProcessed(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.HAWK_REQUEST_ALREADY_PROCESSED.value,
            debug_message=message
            or "A request with the same nonce has already been processed",
            status_code=403,
        )


class HawkMacMismatch(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.HAWK_MAC_MISMATCH.value,
            debug_message=message
            or "The mac send in the request doesn't match the match",
            status_code=403,
        )


class HawkTokenExpired(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.HAWK_TOKEN_EXPIRED.value,
            debug_message=message or "The timestamp sent in the request has expired",
            status_code=403,
        )


class HawkMisComputedContentHash(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.HAWK_MIS_COMPUTED_CONTENT_HASH.value,
            debug_message=message or "The content hash doesn't match",
            status_code=403,
        )


class HawkInvalidUserKey(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.HAWK_INVALID_USER_KEY.value,
            debug_message=message
            or "The provided user key is invalid, it should look like this user_id.auth_id",
            status_code=403,
        )
