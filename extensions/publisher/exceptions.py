from sdk.common.exceptions.exceptions import ErrorCodes, DetailedException


class PublisherErrorCodes(ErrorCodes):
    DUPLICATE_PUBLISHER_NAME = 1100001


class DuplicatePublisherName(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=PublisherErrorCodes.DUPLICATE_PUBLISHER_NAME,
            debug_message=message or "Publisher with that name already exists.",
            status_code=400,
        )
