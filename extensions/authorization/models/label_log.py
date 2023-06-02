from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field


@convertibleclass
class LabelLog:
    """Model to store label logs in db."""

    ID = "id"
    USER_ID = "userId"
    ASSIGNEE_ID = "assigneeId"
    LABEL_ID = "labelId"
    CREATE_DATE_TIME = "createDateTime"

    id: str = default_field()
    userId: str = required_field()
    assigneeId: str = required_field()
    labelId: str = required_field()
    createDateTime: str = default_field()
