from sdk.common.exceptions.exceptions import DetailedException


class DashboardErrorCodes:
    INVALID_GADGET_TYPE = 610000


class InvalidGadgetException(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DashboardErrorCodes.INVALID_GADGET_TYPE,
            debug_message=message or "Invalid gadget type",
            status_code=404,
        )
