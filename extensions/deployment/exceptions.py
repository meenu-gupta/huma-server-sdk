from sdk.common.exceptions.exceptions import DetailedException


class DeploymentErrorCodes:
    INVALID_DEPLOYMENT_ID = 300012
    INVALID_CONSENT_ID = 300013
    PERMISSION_ERROR = 300014
    CONSENT_NOT_SIGNED = 300015
    INVALID_MODULE_CONFIGURATION = 300016
    CONSENT_ALREADY_SIGNED = 300017
    INVALID_DEPLOYMENT_ID_WITH_VERSION_NUMBER = 300018
    INVALID_ECONSENT_ID = 300019
    ECONSENT_ALREADY_SIGNED = 300020
    ECONSENT_NOT_SIGNED = 300021
    ECONSENT_PDF_GENERATION = 300022
    OFF_BOARDING = 300023
    DUPLICATE_ROLE_NAME = 300024
    NOT_PART_OF_DEPLOYMENT = 300025
    INVALID_ROLE_ID = 300026
    ONBOARDING_ERROR = 300027
    AZ_PRESCREENING_NEEDED = 300028
    HELPER_AGREEMENT_NEEDED = 300029
    INVALID_DEPLOYMENT = 300030
    PREFERRED_UNITS_MODULE_NEEDED = 300031
    MODULE_WITH_PRIMITIVE_DOES_NOT_EXIST = 300032
    OFF_BOARDING_USER_NO_CONSENT = 300033
    OFF_BOARDING_USER_FAIL_ID_VERIFICATION = 300034
    OFF_BOARDING_USER_FAIL_PRE_SCREENING = 300035
    OFF_BOARDING_USER_COMPLETE_ALL_TASK = 300036
    OFF_BOARDING_USER_MANUAL_OFF_BOARDED = 300037
    OFF_BOARDING_USER_FAIL_HELPER_AGREEMENT = 300038
    OFF_BOARDING_USER_UNSIGNED_EICF = 300039
    OFF_BOARDING_USER_WITHDRAW_EICF = 300040
    OPTIONS_LIBRARY_FAIL_VALIDATION = 300041
    DUPLICATE_LABEL_NAME = 300042
    MAX_DEPLOYMENT_LABELS_CREATED = 300043


class ConsentNotSignedError(DetailedException):
    """If user haven't yet signed latest consent."""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.CONSENT_NOT_SIGNED,
            debug_message=message or "Latest consent is not signed",
            status_code=428,
        )


class DeploymentDoesNotExist(DetailedException):
    """If Deployment doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_DEPLOYMENT_ID,
            debug_message=message or "Deployment Doesn't Exist.",
            status_code=404,
        )


class DuplicateRoleName(DetailedException):
    """Raise when trying to create a role that is already created in our system."""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.DUPLICATE_ROLE_NAME,
            debug_message=message or "Custom Role Name Already Exists.",
            status_code=400,
        )


class DuplicateLabel(DetailedException):
    """Raise when trying to create a label that is already exist in a deployment."""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.DUPLICATE_LABEL_NAME,
            debug_message=message or "Label Name Already Exists.",
            status_code=400,
        )


class DeploymentWithVersionNumberDoesNotExist(DetailedException):
    """If Deployment with version number doesn't exist."""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_DEPLOYMENT_ID_WITH_VERSION_NUMBER,
            debug_message=message
            or "Deployment with the version number Doesn't Exist.",
            status_code=404,
        )


class ConsentDoesNotExist(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_CONSENT_ID,
            debug_message=message or "Consent Doesn't Exist.",
            status_code=404,
        )


class ConsentSignedError(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.CONSENT_ALREADY_SIGNED,
            debug_message=message or "Latest consent is already signed by this user.",
            status_code=400,
        )


class DeploymentOrObjectDoesNotExist(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_DEPLOYMENT_ID,
            debug_message=message or "Deployment or Object does not exist",
            status_code=404,
        )


class EConsentDoesNotExist(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_ECONSENT_ID,
            debug_message=message or "EConsent Doesn't Exist.",
            status_code=404,
        )


class EConsentSignedError(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.ECONSENT_ALREADY_SIGNED,
            debug_message=message or "Latest EConsent is already signed by this user.",
            status_code=400,
        )


class EConsentLogDoesNotExist(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_ECONSENT_ID,
            debug_message=message or "No signed EConsent",
            status_code=404,
        )


class EConsentNotSignedError(DetailedException):
    """If user haven't yet signed latest econsent."""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.ECONSENT_NOT_SIGNED,
            debug_message=message or "Latest econsent is not signed",
            status_code=428,
        )


class EConsentPdfGenerationError(DetailedException):
    """If there was an error while generating pdf"""

    def __init__(self, error):
        super().__init__(
            code=DeploymentErrorCodes.ECONSENT_PDF_GENERATION,
            debug_message=f"PDF Generation Error. Error: {error}",
            status_code=428,
        )


class OffBoardingRequiredError(DetailedException):
    """Force user to be off-boarded."""

    def __init__(self, code: int = None):
        super().__init__(
            code=code,
            debug_message="User off-boarding required.",
            status_code=412,
        )


class NotPartOfTheSameDeployment(DetailedException):
    """Raise when trying to set roles, but deployments are different"""

    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.NOT_PART_OF_DEPLOYMENT,
            debug_message=message or "Not part of the same deployment",
            status_code=400,
        )


class PatientIdentifiersPermissionDenied(DetailedException):
    def __init__(self, message=False):
        super().__init__(
            code=DeploymentErrorCodes.PERMISSION_ERROR,
            debug_message=message or "Patient Identifiers not allowed for this user",
            status_code=403,
        )


class InvalidDeploymentException(DetailedException):
    def __init__(self, msg=None):
        super().__init__(
            code=DeploymentErrorCodes.INVALID_DEPLOYMENT,
            debug_message=msg or "Deployment is not valid",
            status_code=400,
        )


class ModuleWithPrimitiveDoesNotExistException(DetailedException):
    def __init__(self, msg=None):
        super().__init__(
            code=DeploymentErrorCodes.MODULE_WITH_PRIMITIVE_DOES_NOT_EXIST,
            debug_message=msg or "Module with primitive doesn't exist",
            status_code=404,
        )


class HumaOptionLibraryInvalidDataException(DetailedException):
    def __init__(self, msg=None):
        super().__init__(
            code=DeploymentErrorCodes.OPTIONS_LIBRARY_FAIL_VALIDATION,
            debug_message=msg or "File is not valid for options library",
            status_code=403,
        )


class MaxDeploymentLabelsCreated(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            code=DeploymentErrorCodes.MAX_DEPLOYMENT_LABELS_CREATED,
            debug_message=message or "Deployment already has maximum number of labels",
            status_code=400,
        )
