from datetime import datetime

from extensions.module_result.models.module_config import CustomModuleConfigLog
from sdk import convertibleclass
from sdk.common.utils.convertible import default_field, meta
from sdk.common.usecase.response_object import Response


@convertibleclass
class Flags:
    RED = "red"
    AMBER = "amber"
    GRAY = "gray"

    red: int = default_field()
    amber: int = default_field()
    gray: int = default_field()


@convertibleclass
class UnseenModuleResult:
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"
    FLAGS = "flags"

    moduleId: str = default_field()
    moduleConfigId: str = default_field(metadata=meta(value_to_field=str))
    flags: Flags = default_field()


@convertibleclass
class UnseenModulesResponse:
    FLAGS = "flags"
    LAST_MANAGER_NOTE = "lastManagerNote"

    flags: list[UnseenModuleResult] = default_field()
    lastManagerNote: datetime = default_field()


class CustomModuleConfigLogResponseObject(Response):
    @convertibleclass
    class Response:
        LOGS = "logs"
        TOTAL = "total"

        logs: list[CustomModuleConfigLog] = default_field()
        total: int = default_field()

    def __init__(
        self, logs: list[CustomModuleConfigLog], total: int
    ):
        super().__init__(
            value=self.Response(logs=logs, total=total)
        )
