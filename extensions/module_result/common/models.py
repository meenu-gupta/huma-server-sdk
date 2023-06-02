from datetime import datetime

from sdk import convertibleclass, meta
from sdk.common.utils.convertible import default_field
from sdk.common.utils.validators import (
    validate_object_id,
    default_datetime_meta,
)


@convertibleclass
class MultipleValuesData:
    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    p: dict = default_field()
    d: datetime = default_field(metadata=default_datetime_meta())


@convertibleclass
class MultipleHourValuesData(MultipleValuesData):
    h: dict = default_field()

    def post_init(self):
        if not self.h and self.p:
            self.h = self.parse_p_to_h(self.p)
            self.p = None

    @staticmethod
    def parse_p_to_h(p):
        return {"0": sum([p[x] for x in p])}
