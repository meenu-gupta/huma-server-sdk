from dataclasses import field
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import default_field
from sdk.common.utils.validators import validate_id, validate_datetime


@convertibleclass
class DeploymentEvent:
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    LEARN_ARTICLE_ID = "learnArticleId"

    title: str = default_field()
    description: str = default_field()
    enabled: bool = field(default=True)
    startDateTime: str = default_field(metadata=meta(validate_datetime))
    endDateTime: str = default_field(metadata=meta(validate_datetime))
    keyActionConfigId: str = default_field(metadata=meta(validate_id))
    model: str = default_field()
    moduleConfigId: str = default_field()
    moduleId: str = default_field()
    learnArticleId: str = default_field(metadata=meta(validate_id))
