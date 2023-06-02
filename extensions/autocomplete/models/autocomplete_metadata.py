from datetime import datetime

from extensions.common.s3object import S3Object
from sdk import convertibleclass
from sdk.common.localization.utils import Language
from sdk.common.utils.convertible import required_field, meta, default_field
from sdk.common.utils.validators import (
    incorrect_language_to_default,
    default_datetime_meta,
)


@convertibleclass
class AutocompleteMetadata:
    MODULE_ID = "moduleId"
    LANGUAGE = "language"
    S3_OBJECT = "s3Object"
    UPDATE_DATE_TIME = "updateDateTime"

    moduleId: str = required_field()
    language: str = required_field(
        default=Language.EN, metadata=meta(value_to_field=incorrect_language_to_default)
    )
    s3Object: S3Object = required_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
