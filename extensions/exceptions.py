from sdk.common.exceptions.exceptions import DetailedException, ErrorCodes


class MedicationErrorCodes:
    INVALID_MEDICATION_ID = 400011


class AppointmentErrorCodes:
    INVALID_APPOINTMENT_ID = 500010


class OrganizationErrorCodes:
    INVALID_ORGANIZATION_ID = 600010
    DEPLOYMENT_ALREADY_EXISTS = 600011
    DEPLOYMENT_CODE_ALREADY_EXISTS = 600012
    DUPLICATE_ORGANIZATION_NAME = 600013
    DEPLOYMENT_NOT_LINKED = 600014


class KardioErrorCodes:
    PDF_GENERATION_ERROR = 700010


class RoleErrorCodes:
    PROXY_ALREADY_LINKED = 800001
    PROXY_UNLINKED = 800002
    ROLE_DOES_NOT_EXIST = 800003
    ROLE_ALREADY_EXISTS = 800004


class UserErrorCodes(ErrorCodes):
    INVALID_SURGERY_DATE = 1000001
    INVALID_USER_ID = 1000002
    OUTDATED_ECONSENT = 1000003
    WITHDRAWN_ECONSENT = 1000004


class InvalidSurgeryDateError(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=UserErrorCodes.INVALID_SURGERY_DATE,
            debug_message=message or "Invalid Surgery Date",
            status_code=400,
        )


class EconsentWithdrawalError(DetailedException):
    def __init__(self, message=False, code: int = None):
        super().__init__(
            code=code or UserErrorCodes.OUTDATED_ECONSENT,
            debug_message=message or "Error while withdrawing Econsent",
            status_code=400,
        )


class UserWithdrewEconsent(DetailedException):
    def __init__(self, message=False, code: int = None):
        super().__init__(
            code=code or UserErrorCodes.WITHDRAWN_ECONSENT,
            debug_message=message or "Cant reactivate user with withdrawn econsent",
            status_code=400,
        )


class UserDoesNotExist(DetailedException):
    """If user doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=UserErrorCodes.INVALID_USER_ID,
            debug_message=message or "User Doesn't Exist.",
            status_code=404,
        )


class ValidationDataError(DetailedException):
    """If validation data is not provided."""

    def __init__(self, message=False):
        super().__init__(
            code=ErrorCodes.DATA_VALIDATION_ERROR,
            debug_message=message or "Validation Data Error",
            status_code=400,
        )


class RevereTestDoesNotExist(DetailedException):
    """If revere test doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Test Doesn't Exist.",
            status_code=404,
        )


class MedicationDoesNotExist(DetailedException):
    """If Medication doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=MedicationErrorCodes.INVALID_MEDICATION_ID,
            debug_message=message or "Medication Doesn't Exist.",
            status_code=404,
        )


class LearnSectionDoesNotExist(DetailedException):
    """If learn section doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Learn Section Doesn't Exist.",
            status_code=404,
        )


class LearnArticleDoesNotExist(DetailedException):
    """If learn article doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Learn Article Doesn't Exist.",
            status_code=404,
        )


class AppointmentDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=AppointmentErrorCodes.INVALID_APPOINTMENT_ID,
            debug_message=message or "Appointment does not exist",
            status_code=404,
        )


class ParametersDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "Parameter doesn't exit.",
            status_code=404,
        )


class EncryptionSecretNotAvailable(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.ENCRYPTION_FAILED,
            debug_message=message or "Encryption secret not available",
            status_code=404,
        )


class HttpErrorOnPamQuestionnaire(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=message or "HTTP Error from PAM Survey URL",
            status_code=400,
        )


class OrganizationDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=OrganizationErrorCodes.INVALID_ORGANIZATION_ID,
            debug_message=message or "Organization does not exist",
            status_code=404,
        )


class DeploymentNotLinked(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=OrganizationErrorCodes.DEPLOYMENT_NOT_LINKED,
            debug_message=message or "Deployment is not linked",
            status_code=400,
        )


class DuplicateOrganizationNameException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=OrganizationErrorCodes.DUPLICATE_ORGANIZATION_NAME,
            debug_message=message or "Organization with same name already exists.",
            status_code=400,
        )


class DeploymentExists(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=OrganizationErrorCodes.DEPLOYMENT_ALREADY_EXISTS,
            debug_message=message or "Deployment already exists in this organization",
        )


class DeploymentCodeExists(DetailedException):
    def __init__(self, code: str):
        super().__init__(
            code=OrganizationErrorCodes.DEPLOYMENT_CODE_ALREADY_EXISTS,
            debug_message=f"Deployment with code {code} already exists in this organization",
        )


class ECGPdfGenerationError(DetailedException):
    """If any exception has been risen on ecg pdf generation"""

    def __init__(self, message=None):
        super().__init__(
            code=KardioErrorCodes.PDF_GENERATION_ERROR,
            debug_message=message or f"PDF Generation Error.",
            status_code=500,
        )


class OnboardingError(DetailedException):
    """Raise an error when user needs to complete actions on onboarding"""

    def __init__(self, config_id=None, code: int = None):
        super().__init__(
            code=code,
            debug_message=f"{config_id} is required to be finished.",
            status_code=428,
        )


class ProxyAlreadyLinkedException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=RoleErrorCodes.PROXY_ALREADY_LINKED,
            debug_message=message or f"Proxy user already linked",
        )


class RoleAlreadyExistsException(DetailedException):
    def __init__(self, role, message=None):
        super().__init__(
            code=RoleErrorCodes.ROLE_ALREADY_EXISTS,
            debug_message=message or f"Role: {role} already exists for this user",
        )


class RoleDoesNotExistException(DetailedException):
    def __init__(self, role: str, message=None):
        super().__init__(
            code=RoleErrorCodes.ROLE_DOES_NOT_EXIST,
            debug_message=message or f"Role {role} does not exist for this user",
        )


class ProxyUnlinkedException(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=RoleErrorCodes.PROXY_UNLINKED,
            debug_message=message or "Proxy unlinked",
            status_code=403,
        )


class EConsentInvalidAdditionalConsentAnswersException(DetailedException):
    def __init__(self, question_types=None):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"EConsent Additional Consent Question type [{question_types}] is/are not valid.",
            status_code=400,
        )
