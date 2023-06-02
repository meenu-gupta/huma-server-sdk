import logging
import sys
import traceback

import flask
import yaml
from celery import Celery
from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from mongoengine import connect
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError, OperationFailure
from qcloud_cos import CosConfig
from redis import Redis

from sdk.celery.app import celery_app
from sdk.common.adapter.alibaba.ali_cloud_push_adaptor import AliCloudPushAdapter
from sdk.common.adapter.alibaba.ali_cloud_push_config import AliCloudPushConfig
from sdk.common.adapter.alibaba.ali_cloud_sms_adapter import AliCloudSmsAdapter
from sdk.common.adapter.alibaba.ali_cloud_sms_verification_adapter import (
    AliCloudSmsVerificationAdapter,
)
from sdk.common.adapter.alibaba.oss_file_adapter import OSSFileStorageAdapter
from sdk.common.adapter.apns.apns_push_adapter import APNSPushAdapter
from sdk.common.adapter.apns.apns_push_config import APNSPushConfig
from sdk.common.adapter.azure.azure_blob_storage_adapter import AzureBlobStorageAdapter
from sdk.common.adapter.email.mailgun_email_adapter import (
    MailgunEmailAdapter,
    DebugEmailAdapter,
)
from sdk.common.adapter.email_adapter import EmailAdapter
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.adapter.fcm.fcm_push_adapter import FCMPushAdapter
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.adapter.gcp.gcs_file_storage_adapter import GCSFileStorageAdapter
from sdk.common.adapter.minio.minio_file_storage_adapter import MinioFileStorageAdapter
from sdk.common.adapter.mongodb.mongo_one_time_passowrd_repository import (
    MongoOneTimePasswordRepository,
)
from sdk.common.adapter.mongodb.mongodb_utils import db_is_accessible
from sdk.common.adapter.monitoring_adapter import MonitoringAdapter
from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
from sdk.common.adapter.redis.redis_utils import cache_is_accessible
from sdk.common.adapter.sentry.sentry_adapter import SentryAdapter
from sdk.common.adapter.sms_adapter import SmsAdapter
from sdk.common.adapter.sms_verification_adapter import SmsVerificationAdapter
from sdk.common.adapter.tencent.tencent_cloud_cos_file_storage_adapter import (
    TencentCosFileStorageAdapter,
)
from sdk.common.adapter.token.jwt_token_adapter import JwtTokenAdapter
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.adapter.twilio.exceptions import TwilioErrorCodes
from sdk.common.adapter.twilio.twilio_sms_adapter import TwilioSmsAdapter
from sdk.common.adapter.twilio.twilio_sms_verification_adapter import (
    TwilioSmsVerificationAdapter,
)
from sdk.common.adapter.twilio.twilio_video_adapter import TwilioVideoAdapter
from sdk.common.caching.repo.caching_repo import CachingRepository
from sdk.common.caching.repo.redis_caching_repo import RedisCachingRepository
from sdk.common.exceptions.exceptions import DetailedException
from sdk.common.localization.middleware import LocalizationMiddleware
from sdk.common.localization.utils import Localization
from sdk.common.logging.middleware import RequestErrorHandlerMiddleware
from sdk.common.requests.middleware import RequestContextMiddleware
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.common.utils.token.exceptions import NoAuthorizationError
from sdk.common.utils.url_utils import clean_password_from_url
from sdk.phoenix.component_manager import PhoenixComponentManager
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.helpers import configure_swagger, configure_rate_limit

logger = logging.getLogger(__name__)
VERSION = "0.0.1-beta"

MIDDLEWARES = (
    RequestErrorHandlerMiddleware,
    RequestContextMiddleware,
    LocalizationMiddleware,
)


def setup_di(
    config: PhoenixServerConfig,
    component_manager: PhoenixComponentManager,
    api_specs: list = None,
    clear=False,
    server_version: str = None,
    localization_path: str = None,
):
    def configure_with_binder(binder: Binder):
        # bind Config
        binder.bind(PhoenixServerConfig, config)
        # bind app
        bind_app(binder, config, api_specs)
        # bind celery app and tasks if present
        bind_celery_app(binder, config, component_manager)
        # bind localization data
        bind_localization_data(binder, localization_path)
        # bind event bus adapter
        bind_event_bus_adapter(binder, config)
        # bind db client and default Database
        bind_db_client_and_database(binder, config)
        bind_cache_client_and_repo(binder, config)
        # bind fcm & apns
        bind_fcm_push_notification_adapter(binder, config)
        bind_apns_push_notification_adapter(binder, config)
        # bind sms
        bind_twilio_sms_adapter(binder, config)
        bind_twilio_push_notification_adapter(binder, config)
        bind_twilio_verification_adapter(binder, config)
        bind_ali_cloud_sms_adapter(binder, config)
        bind_ali_cloud_sms_verification_adapter(binder, config)
        # bind ali cloud push
        bind_ali_cloud_push_adapter(binder, config)
        # bind email
        bind_mailgun_email_adapter(binder, config)
        # bind file storage
        bind_tencent_cos_file_storage_adapter(binder, config)
        bind_oss_file_storage_adapter(binder, config)
        bind_minio_file_storage_adapter(binder, config)
        bind_gcs_file_storage_adapter(binder, config)
        bind_azure_file_storage_adapter(binder, config)

        # bind twilio video adapter
        bind_twilio_video_adapter(binder, config)

        # bind jwt token
        bind_jwt_token_adapter(binder, config)
        # db related repo
        bind_one_time_password_repository(binder, config)
        # mailgun verification adapter
        bind_email_verification_adapter(binder)
        # mailgun confirmation adapter
        bind_email_confirmation_adapter(binder)
        # sentry adapter
        bind_sentry_adapter(binder, config, server_version)
        # bind component manager
        binder.bind(PhoenixComponentManager, component_manager)
        # extra binder
        for component in component_manager.components:
            component.bind(binder, config)

    if clear:
        inject.clear_and_configure(configure_with_binder)
    else:
        inject.configure(configure_with_binder)


def bind_app(binder: Binder, config: PhoenixServerConfig, api_specs: list):
    flask_app = flask.app.Flask(__name__, static_url_path="/static")

    flask_app.config["MAX_CONTENT_LENGTH"] = config.server.maxContentSize
    flask_app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
    if config.server.debug:
        flask_app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
    binder.bind(Flask, flask_app)
    logger.debug(f"flask app configured")

    if config.server.rateLimit and config.server.rateLimit.enable:
        rate_limiter = configure_rate_limit(flask_app, config.server.rateLimit)
        binder.bind(Limiter, rate_limiter)
        logger.debug(f"Rate Limiter configured")

    if config.server.swagger and config.server.swagger.enable:
        swagger = configure_swagger(flask_app, config.server.swagger, api_specs)
        binder.bind(Swagger, swagger)
        logger.debug(f"swagger configured to {config.server.swagger.specs_route}")

    @flask_app.before_request
    def middleware_before_chain():
        for middleware in MIDDLEWARES:
            middleware(request).before_request(request)

    @flask_app.after_request
    def middleware_after_chain(response):
        for middleware in MIDDLEWARES:
            middleware(request).after_request(response)

        return response

    @flask_app.errorhandler(DetailedException)
    def handle_error_middleware_chain(e):
        for middleware in MIDDLEWARES:
            try:
                response, code = middleware(request).handle_exception(e)
                return jsonify(response), code
            except TypeError:
                continue

    @flask_app.errorhandler(NoAuthorizationError)
    def handle_header_error(e: NoAuthorizationError):
        msg = f"errorhandler with no details: {str(e)}\nMore details: {traceback.format_exc()}"
        logger.error(msg)
        exception = DetailedException(
            code=10001, debug_message="no bearer header available", status_code=401
        )
        return exception.to_dict(), exception.status_code

    @flask_app.errorhandler(OperationFailure)
    def handle_mongo_operation_error(error):
        logger.error(f"Mongo OperationFailure error: {error}")
        return jsonify([]), 200

    logger.debug(f"general error handler has been configured")


def bind_twilio_video_adapter(binder, config):
    conf = config.server.adapters.twilioVideo
    if conf is None:
        return

    RequestErrorHandlerMiddleware.INFO_ERROR_CODES.add(
        TwilioErrorCodes.ROOM_ALREADY_CLOSED
    )
    binder.bind_to_provider(TwilioVideoAdapter, lambda: TwilioVideoAdapter(config))
    logger.debug(f"Twilio Video Adapter bind to TwilioVideoAdapter")


def read_config(path: str) -> PhoenixServerConfig:
    logger.debug(f"reading config at path [{path}]")
    with open(path, "r") as stream:
        try:
            return PhoenixServerConfig.from_yaml(stream)
        except yaml.YAMLError as exc:
            logger.fatal(exc)
            sys.exit(1)


def bind_celery_app(
    binder: Binder,
    config: PhoenixServerConfig,
    component_manager: PhoenixComponentManager,
):
    if config.server.celery and config.server.celery.enable:
        celery_app.conf.update(broker_url=config.server.celery.brokerUrl)

        tasks = []
        task_queues = {}
        for component in component_manager.components:
            tasks.extend(component.tasks)
            task_queues.update(component.dedicated_task_queues)
        if tasks:
            tasks = set(tasks)
            logger.debug(f"Tasks to autodiscover: {','.join(tasks)}")
            celery_app.autodiscover_tasks(tasks)
        if task_queues:
            celery_app.conf.update(task_routes=task_queues)

        binder.bind(Celery, celery_app)
        logger.debug(f"Celery bind to Celery App")


def bind_cache_client_and_repo(binder: Binder, config: PhoenixServerConfig):
    redis_config = config.server.adapters.redisDatabase
    redis_client = Redis.from_url(redis_config.url)
    # testing the connection before connecting

    safe_url = clean_password_from_url(redis_config.url)
    if not cache_is_accessible(redis_client):
        raise ConnectionError(f"can not connect to Redis {safe_url}")

    logger.debug(f"Redis client has been connected {safe_url}")
    binder.bind(Redis, redis_client)
    binder.bind(CachingRepository, RedisCachingRepository(redis_client))


def bind_db_client_and_database(binder: Binder, config: PhoenixServerConfig):
    mongo_config = config.server.adapters.mongodbDatabase

    mongodb_db_client = connect(
        host=mongo_config.url, serverSelectionTimeoutMS=10 * 1000
    )

    # testing the connection before connecting
    db = mongodb_db_client[mongo_config.name]

    safe_url = clean_password_from_url(mongo_config.url)
    if not db_is_accessible(db):
        raise PyMongoError(f"can not connect to {safe_url}")

    logger.debug(f"mongodb client has been connected {safe_url}")
    binder.bind(MongoClient, mongodb_db_client)
    binder.bind_to_provider(
        Database, lambda: inject.instance(MongoClient)[mongo_config.name]
    )


def bind_oss_file_storage_adapter(binder: Binder, config: PhoenixServerConfig):
    conf = config.server.adapters.oss
    if conf is None:
        return

    def get_oss_file_storage() -> FileStorageAdapter:
        return OSSFileStorageAdapter(config=conf)

    binder.bind_to_provider("ossFileStorage", get_oss_file_storage)
    minio_conf = config.server.adapters.minio
    if minio_conf is None:
        binder.bind_to_provider(FileStorageAdapter, get_oss_file_storage)

    logger.debug(
        f"Alibaba OSS FileStorageAdapter client configured to qualifier:ossFileAdapter"
    )


def bind_gcs_file_storage_adapter(binder: Binder, config: PhoenixServerConfig):
    conf = config.server.adapters.gcs
    if conf is None:
        return

    def get_gcs_file_storage() -> FileStorageAdapter:
        return GCSFileStorageAdapter(config=conf)

    binder.bind_to_provider("gcsFileStorage", get_gcs_file_storage)
    # we always try to fallback to minio when possible
    minio_conf = config.server.adapters.minio
    if minio_conf is None:
        binder.bind_to_provider(FileStorageAdapter, get_gcs_file_storage)

    logger.debug(
        f"Google GCS FileStorageAdapter client configured to qualifier:gcsFileAdapter"
    )


def bind_azure_file_storage_adapter(binder: Binder, config: PhoenixServerConfig):
    conf = config.server.adapters.azureBlobStorage
    if conf is None:
        return

    def get_azure_file_storage() -> FileStorageAdapter:
        return AzureBlobStorageAdapter(config=conf)

    binder.bind_to_provider("azureFileStorage", get_azure_file_storage)
    # we always try to fallback to minio when possible
    minio_conf = config.server.adapters.minio
    if minio_conf is None:
        binder.bind_to_provider(FileStorageAdapter, get_azure_file_storage)

    logger.debug(
        f"Azure Blob Storage FileStorageAdapter client configured to qualifier:azureBlobStorageFileAdapter"
    )


def bind_minio_file_storage_adapter(binder: Binder, config: PhoenixServerConfig):
    conf = config.server.adapters.minio
    if conf is None:
        return

    def get_minio_file_storage() -> FileStorageAdapter:
        return MinioFileStorageAdapter(config=conf)

    binder.bind_to_provider("minioFileStorage", get_minio_file_storage)
    binder.bind_to_provider(FileStorageAdapter, get_minio_file_storage)
    logger.debug(
        f"Minio FileStorageAdapter client configured to qualifier:ossFileAdapter / and default"
    )


def bind_tencent_cos_file_storage_adapter(binder: Binder, config: PhoenixServerConfig):
    conf = config.server.adapters.tencentCloudCos
    if conf is None:
        return

    def get_cos_file_storage() -> FileStorageAdapter:
        cos_config = CosConfig(
            Region=conf.region,
            SecretId=conf.secretId,
            SecretKey=conf.secretKey,
            Scheme=conf.scheme,
        )
        return TencentCosFileStorageAdapter(cos_config=cos_config)

    binder.bind_to_provider("tencentCloudCosFileStorage", get_cos_file_storage)
    logger.debug(
        f"Tencent Cos FileStorageAdapter client configured to qualifier:cosFileStorage"
    )


def bind_fcm_push_notification_adapter(binder: Binder, config: PhoenixServerConfig):
    push_conf = config.server.adapters.fcmPush
    if not push_conf:
        return

    binder.bind("fcmPushAdapter", FCMPushAdapter(push_conf))
    # this makes it default

    logger.debug(
        f"FCM PushAdapter at path [{push_conf.serviceAccountKeyFilePath}] configured to qualifier:fcmPushAdapter"
    )


def bind_apns_push_notification_adapter(binder: Binder, config: PhoenixServerConfig):
    push_conf: APNSPushConfig = config.server.adapters.apnsPush
    if not push_conf:
        return

    binder.bind("apnsPushAdapter", APNSPushAdapter(push_conf))
    # this makes it default

    logger.debug(
        f"APNS PushAdapter with at [{push_conf.authKeyFilePath}] configured to qualifier:apnsPushAdapter"
    )


def bind_twilio_push_notification_adapter(binder: Binder, config: PhoenixServerConfig):
    push_conf = config.server.adapters.twilioPush
    if not push_conf:
        return

    """
    disabling twilio push for now
    binder.bind('twilioPushAdapter', TwilioPushAdapter(push_conf))
    # this makes it default
    binder.bind(PushAdapter, TwilioPushAdapter(push_conf))
    logger.info(
        f"Twilio PushAdapter with account id [{push_conf.accountSid}] configured to qualifier:twilioPushAdapter"
    )"""


def bind_twilio_sms_adapter(binder: Binder, config: PhoenixServerConfig):
    sms_conf = config.server.adapters.twilioSms
    if not sms_conf:
        return

    binder.bind("twilioSmsAdapter", TwilioSmsAdapter(sms_conf))
    # this makes it default
    binder.bind(SmsAdapter, TwilioSmsAdapter(sms_conf))
    logger.debug(
        f"Twilio SmsAdapter with account id [{sms_conf.accountSid}] configured to qualifier:twilioSmsAdapter"
    )


def bind_ali_cloud_sms_adapter(binder: Binder, config: PhoenixServerConfig):
    sms_conf = config.server.adapters.aliCloudSms
    if not sms_conf:
        return

    binder.bind("aliCloudSmsAdapter", AliCloudSmsAdapter(sms_conf))
    logger.debug(
        f"AliCloud SmsAdapter with template code [{sms_conf.params.templateCode}] "
        + "configured to qualifier:aliCloudSmsAdapter"
    )


def bind_mailgun_email_adapter(binder: Binder, config: PhoenixServerConfig):
    email_conf = config.server.adapters.mailgunEmail

    if email_conf:
        binder.bind(EmailAdapter, MailgunEmailAdapter(email_conf))
        logger.debug(
            f"EmailAdapter bind to MailgunEmailAdapter with domain url [{email_conf.domainUrl}]"
        )
    else:
        binder.bind(EmailAdapter, DebugEmailAdapter())
        logger.debug("EmailAdapter bind to DebugEmailAdapter")


def bind_sentry_adapter(
    binder: Binder,
    config: PhoenixServerConfig,
    server_version: str,
):
    sentry_conf = config.server.adapters.sentry
    if not (sentry_conf and sentry_conf.enable):
        return

    sentry_conf.release = server_version
    binder.bind(MonitoringAdapter, SentryAdapter(sentry_conf))
    logger.debug(f"MonitoringAdapter bind to SentryAdapter")


def bind_one_time_password_repository(binder: Binder, config: PhoenixServerConfig):
    otp_config = config.server.adapters.oneTimePasswordRepo
    if not otp_config:
        return

    binder.bind_to_provider(
        OneTimePasswordRepository, lambda: MongoOneTimePasswordRepository()
    )
    logger.debug("OneTimePasswordRepository bind to MongoOneTimePasswordRepository")


def bind_ali_cloud_sms_verification_adapter(
    binder: Binder, config: PhoenixServerConfig
):
    conf = config.server.adapters.aliCloudSms
    if conf is None:
        return

    binder.bind_to_provider(
        "aliCloudSmsVerificationAdapter",
        lambda: AliCloudSmsVerificationAdapter(
            sms_adapter=inject.instance("aliCloudSmsAdapter")
        ),
    )
    logger.debug(
        "aliCloudSmsVerificationAdapter bind to AliCloudSmsVerificationAdapter"
    )


def bind_ali_cloud_push_adapter(binder: Binder, config: PhoenixServerConfig):
    push_conf: AliCloudPushConfig = config.server.adapters.aliCloudPush
    if not push_conf:
        return

    binder.bind("aliCloudPushAdapter", AliCloudPushAdapter(push_conf))

    logger.debug(f"aliCloudPushAdapter bind to AliCloudPushAdapter")


def bind_twilio_verification_adapter(binder: Binder, config: PhoenixServerConfig):
    ver_conf = config.server.adapters.twilioSmsVerification
    sms_conf = config.server.adapters.twilioSms
    if sms_conf is None and ver_conf is None:
        return

    binder.bind_to_provider(
        "twilioSmsVerificationAdapter",
        lambda: TwilioSmsVerificationAdapter(
            sms_adapter=inject.instance("twilioSmsAdapter"), config=ver_conf
        ),
    )
    binder.bind_to_provider(
        SmsVerificationAdapter,
        lambda: TwilioSmsVerificationAdapter(
            sms_adapter=inject.instance("twilioSmsAdapter"), config=ver_conf
        ),
    )
    logger.debug("twilioSmsVerificationAdapter bind to TwilioSmsVerificationAdapter")


def bind_jwt_token_adapter(binder: Binder, config: PhoenixServerConfig):
    jwt_conf = config.server.adapters.jwtToken
    if jwt_conf is None:
        return

    binder.bind_to_provider("jwtTokenAdapter", lambda: JwtTokenAdapter(jwt_conf))
    binder.bind_to_provider(TokenAdapter, lambda: JwtTokenAdapter(jwt_conf))
    logger.debug("jwtTokenAdapter bind to JwtTokenAdapter")


def bind_email_verification_adapter(binder: Binder):
    binder.bind_to_provider(
        "emailVerificationAdapter",
        lambda: EmailVerificationAdapter(),
    )
    binder.bind_to_provider(
        EmailVerificationAdapter,
        lambda: EmailVerificationAdapter(),
    )
    logger.debug("emailVerificationAdapter bind to EmailVerificationAdapter")


def bind_email_confirmation_adapter(binder: Binder):
    binder.bind_to_provider(
        EmailConfirmationAdapter,
        lambda: EmailConfirmationAdapter(),
    )
    logger.debug("EmailConfirmationAdapter bind to emailConfirmationAdapter")


def bind_event_bus_adapter(binder: Binder, config: PhoenixServerConfig):
    binder.bind(EventBusAdapter, EventBusAdapter())
    logger.debug("EventBusAdapter bind to EventBusAdapter()")


def bind_localization_data(binder: Binder, localization_path: str):
    localization = Localization(localization_path)
    binder.bind(Localization, localization)
    logger.debug(f"Localization configured")
