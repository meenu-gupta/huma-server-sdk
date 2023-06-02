from dataclasses import field
from datetime import datetime
from enum import Enum

from extensions.authorization.models.user import User
from extensions.common.s3object import S3Object
from extensions.module_result.models.primitives import Primitive
from sdk import convertibleclass, meta
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_object_id,
    default_datetime_meta,
    validate_id,
    start_datetime_from_str_or_date,
    end_datetime_from_str_or_date,
    string_or_datetime_to_string,
    validate_object_ids,
)

USER_EXCLUDE_FIELDS = (
    User.TAGS,
    User.TAGS_AUTHOR_ID,
    User.ROLES,
    User.RECENT_MODULE_RESULTS,
)

DEFAULT_EXCLUDE_FIELDS = (
    *(f"user.{f}" for f in USER_EXCLUDE_FIELDS),
    Primitive.METADATA,
)

DEFAULT_DEIDENTIFY_HASH_FIELDS = (
    Primitive.ID,
    Primitive.USER_ID,
    Primitive.SUBMITTER_ID,
)

DEFAULT_DEIDENTIFY_REMOVE_FIELDS = (
    User.NHS,
    User.WECHAT_ID,
    User.KARDIA_ID,
    User.INSURANCE_NUMBER,
    User.PAM_THIRD_PARTY_IDENTIFIER,
    User.EMERGENCY_PHONE_NUMBER,
    User.PRIMARY_ADDRESS,
    User.GIVEN_NAME,
    User.FAMILY_NAME,
    User.EMAIL,
    User.PHONE_NUMBER,
    User.ADDITIONAL_CONTACT_DETAILS,
    User.PERSONAL_DOCUMENTS,
    User.FAMILY_MEDICAL_HISTORY,
    User.EXTRA_CUSTOM_FIELDS,
    User.BIOLOGICAL_SEX,
    User.DATE_OF_BIRTH,
    Primitive.DEPLOYMENT_ID,
    User.ENROLLMENT_ID,
)


@convertibleclass
class ExportResultObject:
    BUCKET = "bucket"
    KEY = "key"

    bucket: str = required_field()
    key: str = required_field()


@convertibleclass
class ExportParameters:
    INCLUDE_NULL_FIELDS = "includeNullFields"
    FROM_DATE = "fromDate"
    TO_DATE = "toDate"
    VIEW = "view"
    BINARY_OPTION = "binaryOption"
    FORMAT = "format"
    LAYER = "layer"
    QUANTITY = "quantity"
    QUESTIONNAIRE_PER_NAME = "questionnairePerName"
    SPLIT_MULTIPLE_CHOICES = "splitMultipleChoice"
    SPLIT_SYMPTOMS = "splitSymptoms"
    TRANSLATE_PRIMITIVES = "translatePrimitives"
    INCLUDE_USER_META_DATA = "includeUserMetaData"
    DEIDENTIFIED = "deIdentified"
    DEPLOYMENT_ID = "deploymentId"
    DEPLOYMENT_IDS = "deploymentIds"
    ORGANIZATION_ID = "organizationId"
    SINGLE_FILE_RESPONSE = "singleFileResponse"
    TRANSLATION_SHORT_CODES_OBJECT = "translationShortCodesObject"
    TRANSLATION_SHORT_CODES_OBJECT_FORMAT = "translationShortCodesObjectFormat"
    USE_FLAT_STRUCTURE = "useFlatStructure"
    EXCLUDE_FIELDS = "excludeFields"
    INCLUDE_FIELDS = "includeFields"
    USER_IDS = "userIds"
    MODULE_NAMES = "moduleNames"
    ONBOARDING_MODULE_NAMES = "onboardingModuleNames"
    DE_IDENTIFY_REMOVE_FIELDS = "deIdentifyRemoveFields"
    PREFER_SHORT_CODE = "preferShortCode"
    USE_CREATION_TIME = "useCreationTime"

    class DataViewOption(Enum):
        USER = "USER"
        DAY = "DAY"
        MODULE_CONFIG = "MODULE_CONFIG"
        SINGLE = "SINGLE"

    class BinaryDataOption(Enum):
        NONE = "NONE"
        SIGNED_URL = "SIGNED_URL"
        BINARY_INCLUDE = "BINARY_INCLUDE"

    class DataFormatOption(Enum):
        JSON = "JSON"
        CSV = "CSV"
        JSON_CSV = "JSON_CSV"
        PDF = "PDF"

    class DataLayerOption(Enum):
        FLAT = "FLAT"
        NESTED = "NESTED"

    class DataQuantityOption(Enum):
        SINGLE = "SINGLE"
        MULTIPLE = "MULTIPLE"

    fromDate: datetime = default_field(
        metadata=meta(
            field_to_value=string_or_datetime_to_string,
            value_to_field=start_datetime_from_str_or_date,
        ),
    )
    toDate: datetime = default_field(
        metadata=meta(
            field_to_value=string_or_datetime_to_string,
            value_to_field=end_datetime_from_str_or_date,
        ),
    )
    # to export only specific modules
    moduleNames: list[str] = default_field()
    # to export all modules but these
    excludedModuleNames: list[str] = default_field()
    # to export data only for specific users
    userIds: list[str] = default_field(metadata=meta(validate_object_ids))
    # to remove identifiable data from response
    deIdentified: bool = field(default=False)
    # to include fields which have null values, or to remove them
    includeNullFields: bool = field(default=True)
    # to include user's metadata for each primitive
    includeUserMetaData: bool = field(default=True)
    # by default our structure is document-based ( in short json-like structure)
    useFlatStructure: bool = field(default=False)
    # it's a map of questionnaire ids to type when it's not available
    extraQuestionIds: dict = default_field()
    # to select data view, like per Module, per Date, or per User
    view: DataViewOption = field(default=DataViewOption.USER)
    # output files format
    format: DataFormatOption = field(default=DataFormatOption.JSON)
    # to include primitive's binaries in export or to generate signed urls to download them or keep as is
    binaryOption: BinaryDataOption = field(default=BinaryDataOption.BINARY_INCLUDE)
    # should export files be in one folder or separated based on view
    layer: DataLayerOption = field(default=DataLayerOption.NESTED)
    # should result be in one file or in separated by module/day/user per file (csv does not support single file)
    quantity: DataQuantityOption = field(default=DataQuantityOption.MULTIPLE)
    # to split questionnaire primitives into separate files per their name
    questionnairePerName: bool = field(default=False)
    # to split multiple questionnaire choices based on module config
    splitMultipleChoice: bool = field(default=False)
    # to split symptoms in csv format
    splitSymptoms: bool = field(default=False)
    # to translate primitive values into keywords based on provided csv in export deployment config
    translatePrimitives: bool = field(default=False)
    organizationId: str = default_field(metadata=meta(validate_id))
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    singleFileResponse: bool = field(default=False)

    translationShortCodesObject: S3Object = default_field()
    translationShortCodesObjectFormat: DataFormatOption = field(
        default=DataFormatOption.JSON
    )
    # if these fields are set, then only they will be part of export
    includeFields: list[str] = default_field()
    # fields which will be always removed from export
    excludeFields: list[str] = field(default=DEFAULT_EXCLUDE_FIELDS)
    # fields which will be hashed when exporting with "de-identify" option
    deIdentifyHashFields: list[str] = field(default=DEFAULT_DEIDENTIFY_HASH_FIELDS)
    # fields which will be removed when exporting with "de-identify" option
    deIdentifyRemoveFields: list[str] = field(default=DEFAULT_DEIDENTIFY_REMOVE_FIELDS)
    exportBucket: str = default_field()
    onboardingModuleNames: list[str] = default_field()
    # flag to use short codes for questionnaire questions names instead of original one's
    preferShortCode: bool = field(default=False)
    useCreationTime: bool = default_field()


@convertibleclass
class ExportProcess:
    ID = "id"
    STATUS = "status"
    SEEN = "seen"
    RESULT_OBJECT = "resultObject"
    EXPORT_TYPE = "exportType"
    REQUESTER_ID = "requesterId"
    DEPLOYMENT_ID = "deploymentId"
    CREATE_DATE_TIME = "createDateTime"
    TASK_ID = "taskId"

    class ExportStatus(Enum):
        ERROR = "ERROR"
        CREATED = "CREATED"
        PROCESSING = "PROCESSING"
        DONE = "DONE"

    class ExportType(Enum):
        DEFAULT = "DEFAULT"
        USER = "USER"
        SUMMARY_REPORT = "SUMMARY_REPORT"

    id: str = default_field(metadata=meta(validate_object_id))
    resultObject: ExportResultObject = default_field()
    status: ExportStatus = default_field()
    seen: bool = default_field()
    exportParams: ExportParameters = default_field()
    deploymentId: str = default_field(metadata=meta(validate_object_id))
    deploymentIds: list[str] = default_field(metadata=meta(validate_object_ids))
    organizationId: str = default_field(metadata=meta(validate_object_id))
    requesterId: str = default_field(metadata=meta(validate_object_id))
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    exportType: ExportType = default_field()
    taskId: str = default_field()


@convertibleclass
class ExportProfile:
    NAME = "name"
    CONTENT = "content"
    DEPLOYMENT_ID = "deploymentId"
    ORGANIZATION_ID = "organizationId"
    DEFAULT = "default"
    ID = "id"
    ID_ = "_id"
    UPDATE_DATE_TIME = "updateDateTime"

    id: str = default_field(metadata=meta(validate_object_id))
    name: str = default_field()
    content: ExportParameters = default_field()
    deploymentId: str = default_field(metadata=meta(validate_object_id))
    organizationId: str = default_field(metadata=meta(validate_object_id))
    default: bool = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())


class ExportAction(Enum):
    ExportDeployment = "ExportDeployment"
    Export = "Export"
    CreateOrUpdateExportConfig = "CreateOrUpdateExportConfig"
    RunExportDeploymentTask = "RunExportDeploymentTask"

    CreateExportProfile = "CreateExportProfile"
    UpdateExportProfile = "UpdateExportProfile"
    DeleteExportProfile = "DeleteExportProfile"
