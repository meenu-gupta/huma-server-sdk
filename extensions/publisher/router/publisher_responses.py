from sdk import convertibleclass
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import (
    positive_integer_field,
    default_field,
    natural_number_field,
)


class RetrievePublishersResponseObject(Response):
    @convertibleclass
    class Response:
        items: list[dict] = default_field()
        total: int = positive_integer_field(default=None)
        skip: int = positive_integer_field(default=None)
        limit: int = natural_number_field(default=None)

    def __init__(self, items: list[dict], total: int, skip: int, limit: int):
        super().__init__(
            value=self.Response(items=items, total=total, skip=skip, limit=limit)
        )
