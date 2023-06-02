
class TokenException(Exception):
    pass


class NoAuthorizationError(TokenException):
    """
    An error raised when no authorization token was found in a protected endpoint
    """

    pass

