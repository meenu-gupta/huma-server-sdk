import logging
import traceback
from typing import Optional

from extensions.appointment.router.appointment_requests import (
    CreateAppointmentRequestObject,
)
from sdk.common.usecase.use_case import UseCase

logger = logging.getLogger(__name__)


class BaseAppointmentUseCase(UseCase):
    request_object: Optional[CreateAppointmentRequestObject] = None

    def execute(self, request_object):
        self.request_object = request_object
        return super(BaseAppointmentUseCase, self).execute(request_object)

    def process_request(self, request_object):
        raise NotImplementedError
