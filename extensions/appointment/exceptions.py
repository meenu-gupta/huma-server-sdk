from sdk.common.exceptions.exceptions import ErrorCodes, DetailedException


class AppointmentErrorCodes(ErrorCodes):
    INVALID_DATE = 110011
    APPOINTMENT_ALREADY_EXISTS = 110012


class InvalidDateException(DetailedException):
    def __init__(self, message: str):
        super().__init__(
            code=AppointmentErrorCodes.INVALID_DATE,
            debug_message=message,
            status_code=400,
        )


class AppointmentAlreadyExistsException(DetailedException):
    def __init__(self, message: str):
        super().__init__(
            code=AppointmentErrorCodes.APPOINTMENT_ALREADY_EXISTS,
            debug_message=message or "You can not schedule an appointment at this time",
            status_code=400,
        )
