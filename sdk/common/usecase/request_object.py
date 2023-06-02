from sdk.common.utils.convertible import ConvertibleClassValidationError


class RequestObject(object):
    def __nonzero__(self):
        return True

    __bool__ = __nonzero__


class RequestObjectValidationError(ConvertibleClassValidationError):
    """Request object validation error."""
