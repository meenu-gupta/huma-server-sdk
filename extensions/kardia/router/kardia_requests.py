from extensions.authorization.models.user import User
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, meta, default_field
from sdk.common.utils.validators import validate_object_id


@convertibleclass
class CreateKardiaPatientRequestObject:
    EMAIL = "email"
    DOB = "dob"
    USER = "user"

    email: str = required_field()
    dob: str = required_field()
    user: User = required_field()


@convertibleclass
class RetrievePatientRecordingsRequestObject:
    PATIENT_ID = "patientId"

    patientId: str = required_field()


@convertibleclass
class RetrieveSingleEcgRequestObject:
    RECORD_ID = "recordId"

    recordId: str = required_field(metadata=meta(validate_object_id))


@convertibleclass
class RetrieveSingleEcgPdfRequestObject:
    USER_ID = "userId"
    RECORD_ID = "recordId"
    DEPLOYMENT_ID = "deploymentId"

    userId: str = required_field(metadata=meta(validate_object_id))
    recordId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = default_field(metadata=meta(validate_object_id))


@convertibleclass
class SyncKardiaDataRequestObject:
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"

    userId: str = required_field(metadata=meta(validate_object_id))
    deploymentId: str = default_field(metadata=meta(validate_object_id))
