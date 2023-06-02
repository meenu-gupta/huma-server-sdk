from sdk.common.exceptions.exceptions import DetailedException


class RevereErrorCodes:
    HOUNDIFY_ERROR = 140001


class HoundifyException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=RevereErrorCodes.HOUNDIFY_ERROR,
            debug_message=message or "Processing failed",
            status_code=400,
        )
