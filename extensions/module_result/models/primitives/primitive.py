"""model for super primitive"""
from dataclasses import field
from datetime import datetime
from enum import Enum

from extensions.module_result.exceptions import PrimitiveNotRegisteredException
from sdk.common.utils import inject
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import (
    not_empty,
    validate_object_id,
    default_datetime_meta,
    validate_entity_name,
    str_id_to_obj_id,
    default_version_meta,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.versioning.models.version import Version
from sdk.versioning.models.version_field import VersionField
from sdk.versioning.user_agent_parser import UserAgent


class ChangeDirection(Enum):
    DECREASED = "DECREASED"
    INCREASED = "INCREASED"
    NOCHANGE = "NOCHANGE"


class MeasureUnit(Enum):
    """
    All possible units for any Medical/Health data
    """

    CELSIUS = "oC"
    FAHRENHEIT = "oF"
    BEATS_PER_MINUTE = "bpm"
    MILLIMETRES_MERCURY = "mmHg"
    RESPIRATIONS_PER_MINUTE = "rpm"
    PERCENTAGE = "%"
    MILLIMOLES_PER_LITRE = "mmol/L"
    MILLIGRAMS_PER_DECILITRE = "mg/dL"
    POUNDS = "lb"
    STONES_AND_POUNDS = "St and lbs"
    KILOGRAM = "kg"
    INCH = "in"
    CENTIMETRE = "cm"
    FEET_AND_INCH = "feet and in"
    KILOGRAM_PER_CENTIMETER = "kg/cm2"
    LITRE_PER_SECOND = "L/s"
    LITRE_PER_MINUTE = "L/min"

    @staticmethod
    def get_value_list():
        return list(map(lambda m: m.value, MeasureUnit))


class HumaMeasureUnit(Enum):
    """
    Default internal Huma measure units
    """

    TEMPERATURE = MeasureUnit.CELSIUS.value
    HEART_RATE = MeasureUnit.BEATS_PER_MINUTE.value
    BLOOD_PRESSURE = MeasureUnit.MILLIMETRES_MERCURY.value
    RESPIRATORY_RATE = MeasureUnit.RESPIRATIONS_PER_MINUTE.value
    OXYGEN_SATURATION = MeasureUnit.PERCENTAGE.value
    BLOOD_GLUCOSE = MeasureUnit.MILLIMOLES_PER_LITRE.value
    WEIGHT = MeasureUnit.KILOGRAM.value
    WAIST_CIRCUMFERENCE = MeasureUnit.CENTIMETRE.value
    HIP_CIRCUMFERENCE = MeasureUnit.CENTIMETRE.value
    HEIGHT = MeasureUnit.CENTIMETRE.value
    BMI = MeasureUnit.KILOGRAM_PER_CENTIMETER.value
    PEAK_FLOW = MeasureUnit.LITRE_PER_SECOND.value

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_


@convertibleclass
class Server:
    HOST_URL = "hostUrl"
    SERVER = "server"
    API = "api"

    hostUrl: str = required_field()
    server: VersionField = required_field(metadata=default_version_meta())
    api: str = required_field()


@convertibleclass
class Primitive:
    ID_ = "_id"
    ID = "id"
    USER_ID = "userId"
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"
    MODULE_RESULT_ID = "moduleResultId"
    DEPLOYMENT_ID = "deploymentId"
    VERSION = "version"
    DEVICE_NAME = "deviceName"
    DEVICE_DETAILS = "deviceDetails"
    IS_AGGREGATED = "isAggregated"
    AGGREGATION_PRECISION = "aggregationPrecision"
    START_DATE_TIME = "startDateTime"
    END_DATE_TIME = "endDateTime"
    CREATE_DATE_TIME = "createDateTime"
    TABLE_NAME = "tableName"
    SUBMITTER_ID = "submitterId"
    CORRELATION_START_DATE_TIME = "correlationStartDateTime"
    CLIENT = "client"
    SERVER = "server"
    ALLOWED_AGGREGATE_FUNCS = tuple()
    AGGREGATION_FIELDS = tuple()
    CLS = "_cls"
    FIRST_VERSION = 0
    METADATA = "metadata"
    RAG_THRESHOLD = "ragThreshold"
    FLAGS = "flags"

    UNSEEN_PRIMITIVES_COLLECTION = "unseenrecentresult"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    userId: str = required_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    # Note this is the name of the module, not its UUID Id
    moduleId: str = required_field()
    moduleConfigId: str = default_field(metadata=meta(value_to_field=str))
    moduleResultId: str = default_field(metadata=meta(not_empty))
    deploymentId: str = required_field(
        metadata=meta(
            validate_object_id,
            value_to_field=str,
            field_to_value=str_id_to_obj_id,
        ),
    )
    version: int = field(default=FIRST_VERSION)
    deviceName: str = required_field(metadata=meta(validate_entity_name))
    deviceDetails: str = default_field(metadata=meta(validate_entity_name))
    isAggregated: bool = field(default=False)
    aggregationPrecision: str = default_field(metadata=meta(validate_entity_name))
    startDateTime: datetime = field(
        default_factory=datetime.utcnow, metadata=default_datetime_meta()
    )
    endDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = field(
        default_factory=datetime.utcnow, metadata=default_datetime_meta()
    )

    # the id of the user that submitted the primitive entry
    # ex: the id of the manager that submitted the questionnaire for a userId
    submitterId: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )

    # this field indicates the startDateTime of the primitive entry that this entry correlates to
    #  ex. TimedUpAndGo test result + a Questionnaire
    #  the Questionnaire primitive entry will have the TUG test's startDateTime as the correlationStartDateTime
    correlationStartDateTime: datetime = default_field(metadata=default_datetime_meta())

    tags: dict = default_field()
    tagsAuthorId: str = default_field(
        metadata=meta(
            validate_object_id,
            field_to_value=str_id_to_obj_id,
            value_to_field=str,
        ),
    )

    client: UserAgent = default_field()
    server: Server = default_field()

    ragThreshold: dict = default_field()
    flags: dict = default_field()

    def __str__(self):
        temp = f"%s(%s) of user %s for module %s(%s)"
        return temp % (
            type(self).__name__,
            self.id,
            self.userId,
            self.moduleId,
            self.moduleConfigId,
        )

    @property
    def class_name(self):
        return type(self).__name__

    @classmethod
    def create_from_dict(cls, primitive: dict, name: str, validate: bool = True):
        _cls = Primitive.get_class(name)
        return _cls.from_dict(primitive, use_validator_field=validate)

    @staticmethod
    def get_class(name: str):
        for cls in Primitive.__subclasses__():
            if cls.__name__ == name:
                return cls

        raise PrimitiveNotRegisteredException(name=name)

    def create_server_field(self):
        version = inject.instance(Version)
        server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
        host_url = getattr(server_config.server, server_config.server.HOST_URL, None)
        self.server = Server.from_dict(
            {
                Server.HOST_URL: host_url,
                Server.SERVER: version.server,
                Server.API: version.api,
            }
        )


@convertibleclass
class SkippedFieldsMixin:
    SKIPPED = "skipped"
    skipped: list[str] = default_field()

    FIELD_NAMES_TO_EXCLUDE = {SKIPPED}


class Action(Enum):
    CreateModuleResult = "CreateModuleResult"


# Type Hints
Primitives = list[Primitive]
