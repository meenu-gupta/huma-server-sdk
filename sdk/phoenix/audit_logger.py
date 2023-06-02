import json
import logging
from dataclasses import field
from datetime import datetime
from enum import Enum
from functools import wraps
from json import JSONDecodeError
from typing import Any

from flask import g, request

from sdk import convertibleclass
from sdk.common.adapter.audit_adapter import AuditAdapter
from sdk.common.utils import inject
from sdk.common.utils.convertible import required_field, meta, default_field
from sdk.common.utils.sensitive_data import redact_data
from sdk.common.utils.validators import (
    validate_object_id,
    validate_serializable,
    not_empty,
    remove_none_values,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


def get_project_id() -> str:
    server_config = inject.instance(PhoenixServerConfig)
    return server_config.server.project.id


@convertibleclass
class Metadata:
    USER_AGENT = "userAgent"
    PROJECT_ID = "projectId"
    IP_ADDRESS = "ipAddress"
    HOST = "host"

    userAgent: str = default_field(metadata=meta(value_to_field=str))
    projectId: str = field(default_factory=get_project_id)
    ipAddress: str = default_field()
    host: str = default_field()


@convertibleclass
class AuditLog:
    LABEL = "audit"

    ACTION = "action"
    USER_ID = "userId"
    MESSAGE = "message"
    TARGET_ID = "targetId"
    REQUEST_OBJECT = "requestObject"
    RESPONSE_OBJECT = "responseObject"
    METADATA = "metadata"
    CREATE_DATE_TIME = "createDateTime"

    action: str = required_field(metadata=meta(not_empty))
    userId: str = default_field(metadata=meta(validate_object_id))
    message: str = field(default="")
    targetId: str = default_field(metadata=meta(validate_object_id))
    # these fields should accept any serializable data
    requestObject: Any = default_field(metadata=meta(validate_serializable))
    responseObject: Any = default_field(metadata=meta(validate_serializable))
    metadata: Metadata = required_field()
    createDateTime: datetime = field(default_factory=datetime.utcnow)

    def log(self):
        audit_logger = inject.instance(AuditAdapter)
        audit_logger.info(
            label=self.LABEL,
            msg=self.message,
            action=self.action,
            userId=self.userId,
            targetId=self.targetId,
            requestObject=self.requestObject,
            responseObject=self.responseObject,
            metadata=self.metadata.to_dict(),
            createDateTime=self.createDateTime,
        )

    @staticmethod
    def create_log(
        action: Enum,
        user_id: str = None,
        response_object: dict = None,
        target_key: str = None,
        secure: bool = False,
    ):
        metadata = {
            Metadata.HOST: request.host,
            Metadata.IP_ADDRESS: request.remote_addr,
            Metadata.USER_AGENT: request.user_agent,
        }

        try:
            request_object = json.loads(request.get_data())
        except JSONDecodeError:
            request_object = {}

        log_dict = {
            AuditLog.ACTION: action.value,
            AuditLog.USER_ID: user_id,
            AuditLog.REQUEST_OBJECT: {} if secure else redact_data(request_object),
            AuditLog.RESPONSE_OBJECT: {} if secure else redact_data(response_object),
            AuditLog.METADATA: remove_none_values(metadata),
        }

        if target_key:
            log_dict.update({AuditLog.TARGET_ID: request.view_args.get(target_key)})

        log_dict = remove_none_values(log_dict)
        audit_log: AuditLog = AuditLog.from_dict(log_dict)

        try:
            audit_log.log()
        except Exception as e:
            logger.warning(e)


def audit(action: Enum, target_key: str = None, secure: bool = False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response, status = f(*args, **kwargs)
            response_object = response.json if hasattr(response, "json") else {}
            authz_user = g.get("authz_user")

            AuditLog.create_log(
                action=action,
                user_id=authz_user and authz_user.id,
                response_object=response_object,
                target_key=target_key,
                secure=secure,
            )

            return response, status

        return decorated_function

    return decorator
