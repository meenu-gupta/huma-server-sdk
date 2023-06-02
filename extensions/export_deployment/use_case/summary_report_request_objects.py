from dataclasses import field
from datetime import datetime, time
from enum import Enum

from dateutil.relativedelta import relativedelta

from extensions.appointment.exceptions import InvalidDateException
from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.export_deployment.models.export_deployment_models import ExportProcess
from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.convertible import (
    required_field,
    convertibleclass,
    meta,
)
from sdk.common.utils.validators import default_datetime_meta, validate_id


class ReportFormat(Enum):
    PDF = "PDF"


def six_month_ago_from_day_start():
    date = datetime.utcnow() - relativedelta(months=6)
    return datetime.combine(date + relativedelta(days=1), time())


@convertibleclass
class GenerateSummaryReportRequestObject(RequestObject):
    USER = "user"
    DEPLOYMENT = "deployment"
    REQUESTER_ID = "requesterId"
    FORMAT = "format"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"

    user: User = required_field()
    requesterId: str = required_field(metadata=meta(validate_id))
    deployment: Deployment = required_field()
    format: ReportFormat = required_field()
    startDateTime: datetime = field(
        default_factory=six_month_ago_from_day_start,
        metadata=default_datetime_meta(),
    )
    endDateTime: datetime = field(
        default_factory=datetime.utcnow, metadata=default_datetime_meta()
    )

    @classmethod
    def validate(cls, req_obj):
        if req_obj.startDateTime > req_obj.endDateTime:
            raise InvalidDateException("Start date time can't be later than end.")


@convertibleclass
class GenerateSummaryReportAsyncRequestObject(RequestObject):
    """
    Request object for celery task to run async report generation
    @processId - id of the record to update status for
    @taskId - celery task id
    """

    process: ExportProcess = required_field()
    taskId: str = required_field()
