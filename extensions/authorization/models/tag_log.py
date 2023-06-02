from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field


@convertibleclass
class TagLog:
    """Model to store tag logs in db."""

    id: str = default_field()
    userId: str = required_field()
    authorId: str = required_field()
    tags: dict = required_field()
    createDateTime: str = default_field()
