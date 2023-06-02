import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from extensions.authorization.models.action import AuthorizationAction
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.phoenix.audit_logger import AuditLog, Metadata
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server, Project


def sample_log():
    return {
        AuditLog.ACTION: AuthorizationAction.UpdateUser.value,
        AuditLog.USER_ID: "601919b5c03550c421c075eb",
        AuditLog.TARGET_ID: "5ed803dd5f2f99da73684412",
        AuditLog.REQUEST_OBJECT: {"phoneNumber": "+37253551722"},
        AuditLog.RESPONSE_OBJECT: {"id": "5ed803dd5f2f99da73684412"},
        AuditLog.METADATA: {
            Metadata.IP_ADDRESS: "0.0.0.0",
            Metadata.USER_AGENT: "",
            Metadata.HOST: "",
        },
    }


class MockInject:
    project = Project(id="p1")
    server = Server(project=project)
    instance = MagicMock(return_value=PhoenixServerConfig(server=server))


@patch("sdk.phoenix.audit_logger.inject", MockInject)
class AuditLogToDictTestCase(unittest.TestCase):
    def test_success_audit_log_to_dict(self):
        audit_log = AuditLog.from_dict(sample_log())
        self.assertIsNotNone(audit_log)

    def test_failure_missing_required_fields(self):
        required_fields = {AuditLog.ACTION, AuditLog.METADATA}

        for field in required_fields:
            log_dict = sample_log()
            log_dict.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                AuditLog.from_dict(log_dict)

    def test_failure_non_serializable_data(self):
        serializable_fields = {AuditLog.REQUEST_OBJECT, AuditLog.RESPONSE_OBJECT}

        for field in serializable_fields:
            log_dict = sample_log()
            log_dict[field] = ObjectId
            with self.assertRaises(ConvertibleClassValidationError):
                AuditLog.from_dict(log_dict)
