from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import validate_id


@convertibleclass
class ManagerAssignment:
    USER_ID = "userId"
    MANAGER_IDS = "managerIds"
    SUBMITTER_ID = "submitterId"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    userId: str = required_field(metadata=meta(validate_id))
    managerIds: list[str] = required_field(
        metadata=meta(lambda x: all(map(validate_id, x)))
    )
    submitterId: str = required_field(metadata=meta(validate_id))
    updateDateTime: str = default_field()
    createDateTime: str = default_field()
