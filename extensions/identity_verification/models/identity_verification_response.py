from sdk import convertibleclass
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import default_field


class CreateVerificationLogResponseObject(Response):
    @convertibleclass
    class Response:
        message: str = default_field()

    def __init__(self, message: str):
        super().__init__(self.Response(message=message))
