from sdk.common.exceptions.exceptions import DetailedException


class AuthorizationErrorCodes:
    WRONG_ACTIVATION_OR_MASTER_KEY = 1000003
    INVITATION_DOES_NOT_EXIST = 1000004
    CANT_RESEND_INVITATION = 1000005
    INVITATION_IS_EXPIRED = 1000006
    MAX_LABELS_ASSIGNED = 1000007


class WrongActivationOrMasterKeyException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=AuthorizationErrorCodes.WRONG_ACTIVATION_OR_MASTER_KEY,
            debug_message=message or "Activation Code or Master Key is wrong.",
            status_code=400,
        )


class InvitationDoesNotExistException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=AuthorizationErrorCodes.INVITATION_DOES_NOT_EXIST,
            debug_message=message or "Invitation does not exist",
            status_code=404,
        )


class CantResendInvitation(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=AuthorizationErrorCodes.CANT_RESEND_INVITATION,
            debug_message=message or "Can't resend invitation",
            status_code=400,
        )


class InvitationIsExpiredException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=AuthorizationErrorCodes.INVITATION_IS_EXPIRED,
            debug_message=message or "Invitation is expired",
            status_code=400,
        )


class MaxLabelsAssigned(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=AuthorizationErrorCodes.MAX_LABELS_ASSIGNED,
            debug_message=message or "User already has maximum number of labels",
            status_code=400,
        )
