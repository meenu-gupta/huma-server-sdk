from sdk import convertibleclass
from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import positive_integer_field, default_field


class RetrieveOrganizationsResponseObject(Response):
    @convertibleclass
    class Response:
        items: list[dict] = default_field()
        total: int = default_field()
        limit: int = positive_integer_field(default=None)
        skip: int = positive_integer_field(default=None)

    def __init__(self, items: list[dict], total: int, limit: int, skip: int):
        super().__init__(
            value=self.Response(items=items, total=total, limit=limit, skip=skip)
        )
