from sdk.common.adapter.monitoring_adapter import MonitoringAdapter, ErrorForm
from sdk.common.utils import inject


def report_exception(
    error,
    context_name: str = None,
    context_content: dict = None,
    tags: dict[str, str] = None,
):
    monitoring: MonitoringAdapter = inject.instance(MonitoringAdapter)
    if monitoring.is_configured():
        request_body = ErrorForm(error=error)
        if context_name:
            request_body.context = ErrorForm.ContextForm(
                name=context_name, content=context_content
            )
        request_body.tags = tags
        monitoring.report_exception(request_body)
