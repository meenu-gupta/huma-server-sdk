from sdk.common.exceptions.exceptions import DetailedException


class TwilioErrorCodes:
    ROOM_ALREADY_CLOSED = 14001
    INVALID_TOKEN = 14002


class RoomAlreadyClosedException(DetailedException):
    def __init__(self, message=None):
        message = message or "Twilio room does not found. Probably already closed."
        super().__init__(
            code=TwilioErrorCodes.ROOM_ALREADY_CLOSED,
            debug_message=message,
            status_code=400,
        )


class TokenNotValidException(DetailedException):
    def __init__(self, message=None):
        message = message or "Token is not valid."
        super().__init__(
            code=TwilioErrorCodes.INVALID_TOKEN,
            debug_message=message,
            status_code=400,
        )
