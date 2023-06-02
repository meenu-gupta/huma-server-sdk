from dataclasses import field
from datetime import datetime
from enum import Enum

from extensions.deployment.models.localizable import Localizable
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_duration,
    validate_object_id,
    default_datetime_meta,
)


def validate_duration_iso(iso_duration: str) -> bool:
    validate_duration(iso_duration)
    date_duration = iso_duration.split("T")[0]
    durations = ("Y", "M", "W", "D")
    res = []

    for duration in durations:
        if duration in date_duration:
            res.append(duration)
    if len(res) > 1:
        raise Exception(f"Not allowed to use double duration")

    return True


@convertibleclass
class KeyActionConfig(Localizable):
    class Trigger(Enum):
        SIGN_UP = "SIGN_UP"
        SURGERY = "SURGERY"
        MANUAL = "MANUAL"

    class Type(Enum):
        LEARN = "LEARN"
        MODULE = "MODULE"

    ID = "id"
    TITLE = "title"
    DESCRIPTION = "description"
    DELTA_FROM_TRIGGER_TIME = "deltaFromTriggerTime"
    DURATION_FROM_TRIGGER = "durationFromTrigger"
    DURATION_ISO = "durationIso"
    INSTANCE_EXPIRES_IN = "instanceExpiresIn"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    TYPE = "type"
    TRIGGER = "trigger"
    NOTIFY_EVERY = "notifyEvery"
    NUMBER_OF_NOTIFICATIONS = "numberOfNotifications"
    LEARN_ARTICLE_ID = "learnArticleId"
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    title: str = default_field()
    description: str = default_field()
    # deltaFromTriggerTime - duration from trigger datetime to start notifying, i.e. it's 6 month before signup date
    # before 6 month -P6M
    # after 6 month P6M
    deltaFromTriggerTime: str = required_field(metadata=meta(validate_duration))
    # durationFromTrigger - how long continue from the first day of key action being started i.e. 2 months
    durationFromTrigger: str = default_field()  # P2M
    # duration to repeat events i.e. P2DT10H50M - at 10:50am every 2 days
    durationIso: str = required_field(metadata=meta(validate_duration_iso))
    instanceExpiresIn: str = field(default="P1W", metadata=meta(validate_duration))
    type: Type = required_field()
    trigger: Trigger = required_field()

    notifyEvery: str = default_field(metadata=meta(validate_duration))
    numberOfNotifications: int = field(default=2)

    learnArticleId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    moduleId: str = default_field()
    moduleConfigId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )

    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    _localizableFields: tuple[str, ...] = (TITLE, DESCRIPTION)

    def is_for_module(self):
        return self.type == self.Type.MODULE

    def is_for_learn(self):
        return self.type == self.Type.LEARN
