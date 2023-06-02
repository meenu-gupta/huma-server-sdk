from sdk.common.exceptions.exceptions import DetailedException, ErrorCodes


class ModuleResultErrorCodes(ErrorCodes):
    MODULE_NOT_CONFIGURED = 120011
    PRIMITIVE_NOT_REGISTERED = 120012
    PRIMITIVE_NOT_FOUND = 120013
    NOT_ALL_QUESTIONS_ANSWERED = 120014
    INVALID_MODULE_RESULT = 120015


class PrimitiveNotRegisteredException(DetailedException):
    def __init__(self, name):
        super().__init__(
            code=ModuleResultErrorCodes.PRIMITIVE_NOT_REGISTERED,
            debug_message=f"Unknown primitive class: {name}",
            status_code=400,
        )


class InvalidModuleConfiguration(DetailedException):
    """If Module configuration is not valid."""

    def __init__(self, message=None):
        super().__init__(
            code=ModuleResultErrorCodes.MODULE_NOT_CONFIGURED,
            debug_message=message or "Module is not configured.",
            status_code=404,
        )


class PrimitiveNotFoundException(DetailedException):
    """If Module configuration is not valid."""

    def __init__(self, message=None):
        super().__init__(
            code=ModuleResultErrorCodes.PRIMITIVE_NOT_FOUND,
            debug_message=message or "Primitive not found exception",
            status_code=404,
        )


class NotAllRequiredQuestionsAnsweredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ModuleResultErrorCodes.NOT_ALL_QUESTIONS_ANSWERED,
            debug_message=message or "Not all the required questions answered",
            status_code=403,
        )


class InvalidModuleResultException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ModuleResultErrorCodes.INVALID_MODULE_RESULT,
            debug_message=message or "Module result data is not valid",
            status_code=403,
        )
