import abc
from abc import ABC
from dataclasses import field

from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field


@convertibleclass
class ErrorForm:
    ERROR = "error"
    TAGS = "tags"
    CONTEXT = "context"

    @convertibleclass
    class ContextForm:
        name: str = required_field()
        content: dict = default_field()

    error: Exception = required_field()
    tags: dict[str, str] = default_field()
    context: ContextForm = default_field()


class MonitoringAdapter(ABC):
    def is_configured(self) -> bool:
        return False

    def _set_common_information(self, error: ErrorForm):
        pass

    def report_exception(self, error: ErrorForm):
        pass
