from sdk.common.exceptions.exceptions import DetailedException


class ExportErrorCodes:
    DUPLICATE_PROFILE_NAME = 900001
    GENERIC_ERROR = 900002
    PROCESS_IN_PROGRESS = 900003


class DuplicateProfileName(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=ExportErrorCodes.DUPLICATE_PROFILE_NAME,
            debug_message=message or "Profile with that name already exists.",
            status_code=400,
        )


class ExportProcessException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ExportErrorCodes.GENERIC_ERROR,
            debug_message=message or "Generic export error",
            status_code=400,
        )


class ExportProcessIsProgress(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ExportErrorCodes.PROCESS_IN_PROGRESS,
            debug_message=message or "Export process is already running",
            status_code=400,
        )
