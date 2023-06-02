from dataclasses import field
from enum import Enum
from typing import Optional

from sdk.auth.config.auth_config import AuthConfig
from sdk.common.adapter.alibaba.ali_cloud_push_config import AliCloudPushConfig
from sdk.common.adapter.alibaba.ali_cloud_sms_config import AliCloudSmsConfig
from sdk.common.adapter.alibaba.oss_config import OSSConfig
from sdk.common.adapter.apns.apns_push_config import APNSPushConfig
from sdk.common.adapter.azure.azure_blob_storage_config import AzureBlobStorageConfig
from sdk.common.adapter.email.mailgun_config import MailgunConfig
from sdk.common.adapter.fcm.fcm_push_config import FCMPushConfig
from sdk.common.adapter.gcp.gcs_config import GCSConfig
from sdk.common.adapter.minio.minio_config import MinioConfig
from sdk.common.adapter.mongodb.mongodb_config import MongodbDatabaseConfig
from sdk.common.adapter.one_time_password_repository import OneTimePasswordConfig
from sdk.common.adapter.onfido.onfido_config import OnfidoConfig
from sdk.common.adapter.redis.redis_config import RedisDatabaseConfig
from sdk.common.adapter.sentry.sentry_config import SentryConfig
from sdk.common.adapter.tencent.tencent_cloud_cos_config import TencentCloudCosConfig
from sdk.common.adapter.token.jwt_token_config import JwtTokenConfig
from sdk.common.adapter.twilio.twilio_push_config import TwilioPushConfig
from sdk.common.adapter.twilio.twilio_sms_config import TwilioSmsConfig
from sdk.common.adapter.twilio.twilio_sms_verification_config import (
    TwilioSmsVerificationConfig,
)
from sdk.common.adapter.twilio.twilio_video_config import TwilioVideoAdapterConfig
from sdk.common.exceptions.exceptions import MFARequiredException
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.convertible import read_yaml_file
from sdk.common.utils.validators import default_version_meta
from sdk.limiter.config.limiter import ServerLimiterConfig, StorageLimiterConfig
from sdk.versioning.models.version_field import VersionField


class SubscriptableConfig:
    def __getitem__(self, item):
        def type_filter(attr):
            key, value = attr
            decision = True if isinstance(value, item) else False
            return decision

        attr_name = filter(type_filter, self.__dict__.items())
        try:
            config = next(attr_name)[0]
        except StopIteration:
            return None
        return getattr(self, config)


@convertibleclass
class Client:
    CLIENT_ID = "clientId"
    NAME = "name"
    CLIENT_TYPE = "clientType"
    AUTH_TYPE = "authType"
    APP_IDS = "appIds"
    DEEP_LINK_BASE_URL = "deepLinkBaseUrl"
    ROLE_IDS = "roleIds"
    MINIMUM_VERSION = "minimumVersion"
    FINGERPRINTS = "fingerprints"
    SMS_RETRIEVER_CODE = "smsRetrieverCode"

    class ClientType(Enum):
        USER_IOS = "USER_IOS"
        USER_ANDROID = "USER_ANDROID"
        MANAGER_WEB = "MANAGER_WEB"
        USER_WEB = "USER_WEB"
        ADMIN_WEB = "ADMIN_WEB"
        SERVICE_ACCOUNT = "SERVICE_ACCOUNT"

    class AuthType(Enum):
        MFA = "MFA"  # multi-factor authentication only
        SFA = "SFA"  # single-factor authentication

    id: str = default_field()
    name: str = default_field()
    clientId: str = required_field()
    secretKey: str = default_field()
    clientType: ClientType = required_field()
    authType: AuthType = field(default=AuthType.SFA)
    roleIds: list[str] = default_field()
    accessTokenExpiresAfterMinutes: int = field(default=1440)
    refreshTokenExpiresAfterMinutes: int = field(default=1440)
    deepLinkBaseUrl: str = default_field()
    appIds: list[str] = default_field()
    passwordExpiresIn: int = field(default=60)  # days
    minimumVersion: VersionField = default_field(metadata=default_version_meta())
    fingerprints: list[str] = default_field()
    smsRetrieverCode: str = default_field()

    def check_mfa_status(self, mfa_enabled: bool):
        if self.is_mfa_required() and mfa_enabled is False:
            raise MFARequiredException

    def is_mfa_required(self) -> bool:
        return self.authType == self.AuthType.MFA


@convertibleclass
class BasePhoenixConfig:
    enable: bool = field(default=True)
    enableAuth: bool = field(default=True)
    enableAuthz: bool = field(default=True)


@convertibleclass
class SwaggerConfig(BasePhoenixConfig):
    template: dict = default_field()
    specs_route: str = field(default="/apidocs/")

    def post_init(self):
        if not self.specs_route.startswith("/"):
            self.specs_route = "/" + self.specs_route
        if not self.specs_route.endswith("/"):
            self.specs_route += "/"


@convertibleclass
class CeleryConfig(BasePhoenixConfig):
    brokerUrl: str = default_field()


@convertibleclass
class NotificationConfig(BasePhoenixConfig):
    pass


@convertibleclass
class VideoConfig(BasePhoenixConfig):
    pass


@convertibleclass
class AuditLogger(BasePhoenixConfig):
    pass


@convertibleclass
class CalendarConfig(BasePhoenixConfig):
    prefetchDays: int = field(default=7, metadata=meta(lambda n: n >= 0))


@convertibleclass
class FluentdConfig:
    tag: str = field(default="huma")
    host: str = field(default="localhost")
    port: int = field(default=8887)


@convertibleclass
class InboxConfig(BasePhoenixConfig):
    pass


@convertibleclass
class Project:
    ID = "id"
    MASTER_KEY = "masterKey"
    CLIENTS = "clients"

    id: str = required_field()
    name: str = default_field()
    clients: list[Client] = required_field()
    masterKey: str = required_field()
    notFoundLink: str = field(default="https://huma.com/404")

    def get_client_by_id(self, client_id: str) -> Optional[Client]:
        for client in self.clients:
            if client.clientId == client_id:
                return client

    def get_client_by_client_type(
        self, client_type: Client.ClientType
    ) -> Optional[Client]:
        for client in self.clients:
            if client.clientType == client_type:
                return client


@convertibleclass
class HawkTokenConfig:
    hashingAlgorithm: str = field(default="sha256")
    localTimeOffset: int = field(default=0)
    timeStampSkew: int = field(default=60)


@convertibleclass
class Adapters(SubscriptableConfig):
    fluentd: FluentdConfig = default_field()
    twilioSms: TwilioSmsConfig = default_field()
    twilioPush: TwilioPushConfig = default_field()
    twilioVideo: TwilioVideoAdapterConfig = default_field()
    fcmPush: FCMPushConfig = default_field()
    apnsPush: APNSPushConfig = default_field()
    twilioSmsVerification: TwilioSmsVerificationConfig = default_field()
    aliCloudSms: AliCloudSmsConfig = default_field()
    aliCloudPush: AliCloudPushConfig = default_field()
    mailgunEmail: MailgunConfig = default_field()
    tencentCloudCos: TencentCloudCosConfig = default_field()
    oss: OSSConfig = default_field()
    minio: MinioConfig = default_field()
    azureBlobStorage: AzureBlobStorageConfig = default_field()
    gcs: GCSConfig = default_field()
    mongodbDatabase: MongodbDatabaseConfig = default_field()
    redisDatabase: RedisDatabaseConfig = default_field()
    oneTimePasswordRepo: OneTimePasswordConfig = default_field()
    jwtToken: JwtTokenConfig = default_field()
    onfido: OnfidoConfig = default_field()
    sentry: SentryConfig = default_field()
    hawk: HawkTokenConfig = default_field()


class StorageAdapter(Enum):
    MINIO = "MINIO"
    OSS = "OSS"
    GCS = "GCS"
    AZURE = "AZURE"


@convertibleclass
class StorageConfig(BasePhoenixConfig):
    authEnabled: bool = default_field()
    storageAdapter: StorageAdapter = field(default=StorageAdapter.MINIO)
    allowedBuckets: list[str] = default_field()
    defaultBucket: str = default_field()
    rateLimit: StorageLimiterConfig = field(
        default=StorageLimiterConfig(write="10/minute", read="60 per minute")
    )


@convertibleclass
class Server(SubscriptableConfig):
    HOST = "host"
    PORT = "port"
    HOST_URL = "hostUrl"
    WEB_APP_URL = "webAppUrl"
    DEBUG = "debug"
    DEBUG_LOG = "debugLog"
    DEBUG_ROUTER = "debugRouter"
    TEST_ENVIRONMENT = "testEnvironment"
    VERSION = "version"
    MAX_CONTENT_SIZE = "maxContentSize"
    AUDIT_LOGGER = "auditLogger"
    SWAGGER = "swagger"
    CELERY = "celery"
    PROJECT = "project"
    RATE_LIMIT = "rateLimit"
    ADAPTERS = "adapters"
    CALENDAR = "calendar"
    STORAGE = "storage"
    AUTH = "auth"
    INBOX = "inbox"
    COUNTRY_CODE = "countryCode"

    host: str = field(default="0.0.0.0")
    port: int = field(default=5000)
    hostUrl: str = default_field()
    webAppUrl: str = default_field()
    debug: bool = field(default=False)
    debugLog: bool = field(default=False)
    debugRouter: bool = field(default=False)
    testEnvironment: bool = field(default=False)
    version: str = default_field()
    maxContentSize: int = field(default=100 * 1024 * 1024)
    iosAppUrl: str = default_field()
    androidAppUrl: str = default_field()
    countryName: str = default_field()
    countryCode: str = default_field()

    auditLogger: AuditLogger = default_field()
    swagger: SwaggerConfig = default_field()
    celery: CeleryConfig = default_field()
    project: Project = required_field()
    rateLimit: ServerLimiterConfig = default_field()
    adapters: Adapters = required_field()
    calendar: CalendarConfig = field(default=CalendarConfig())
    storage: StorageConfig = default_field()
    auth: AuthConfig = default_field()
    inbox: InboxConfig = default_field()


@convertibleclass
class PhoenixServerConfig(SubscriptableConfig):
    server: Server = required_field()

    @classmethod
    def get(cls, config_file_path, override_config: dict):
        config_dict = read_yaml_file(config_file_path)
        if override_config:
            override_config_fields(config_dict, override_config)

        return cls.from_dict(config_dict)


def apply_argument(config_dict, path, value):
    key = path[0]
    if len(path) == 1:
        if key in config_dict:
            tpe = type(config_dict.get(key))
            if tpe == bool:
                set_value = value == "true" or value == "True"
            elif tpe == int:
                set_value = int(value)
            elif tpe == float:
                set_value = float(value)
            elif tpe == str:
                set_value = value
            elif tpe == list:
                set_value = value
            else:
                raise NotImplementedError

            config_dict[key] = set_value
    else:
        if key in config_dict:
            apply_argument(config_dict[key], path[1:], value)


def override_config_fields(config_dict, args: dict[str, str]):
    if args:
        for key, value in args.items():
            path = key.split(".")
            if path:
                apply_argument(config_dict, path, value)
