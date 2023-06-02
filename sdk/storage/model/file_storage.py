from datetime import datetime
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    default_field,
)
from sdk.common.utils.validators import (
    default_datetime_meta,
    validate_object_id,
)


@convertibleclass
class FileStorage:
    ID_ = "_id"
    ID = "id"
    KEY = "key"
    FILE_NAME = "fileName"
    FILE_SIZE = "fileSize"
    CONTENT_TYPE = "contentType"
    USER_ID = "user_id"
    METADATA = "metadata"
    CREATED_AT = "createdAt"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    key: str = default_field()
    fileName: str = default_field()
    fileSize: int = default_field()
    contentType: str = default_field()
    user_id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    metadata: dict = default_field()
    createdAt: datetime = default_field(metadata=default_datetime_meta())
