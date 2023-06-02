from pathlib import Path
from unittest.mock import patch

from extensions.authorization.component import AuthorizationComponent
from extensions.authorization.models.action import AuthorizationAction
from extensions.authorization.models.user import User
from extensions.deployment.component import DeploymentComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.audit_logger.component import AuditLoggerComponent
from sdk.audit_logger.repo.mongo_audit_log_repository import MongoAuditLogRepository
from sdk.auth.component import AuthComponent
from sdk.phoenix.audit_logger import AuditLog
from sdk.storage.component import StorageComponent

USER_ID = "5e84b0dab8dfa268b1180536"


class AuditedRouteTestCase(ExtensionTestCase):

    components = [
        AuthComponent(),
        AuthorizationComponent(),
        StorageComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        AuditLoggerComponent(),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/organization_dump.json")]

    def setUp(self):
        super().setUp()
        self.base_path = "/api/extensions/v1beta/user"

    @patch.object(AuditLog, "from_dict")
    @patch.object(AuditLog, "log")
    def test_update_profile(self, mock_log, mock_from_dict):
        mock_from_dict.return_value = AuditLog()

        body = {User.HEIGHT: 185}
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_ID}",
            json=body,
            headers=self.get_headers_for_token(USER_ID),
        )
        self.assertEqual(200, rsp.status_code)
        log_dict = mock_from_dict.call_args.args[0]
        self.assertEqual(
            log_dict[AuditLog.ACTION], AuthorizationAction.UpdateUser.value
        )
        self.assertEqual(log_dict[AuditLog.REQUEST_OBJECT], body)
        self.assertEqual(log_dict[AuditLog.RESPONSE_OBJECT], rsp.json)
        self.assertEqual(log_dict[AuditLog.USER_ID], USER_ID)
        self.assertEqual(log_dict[AuditLog.TARGET_ID], USER_ID)

        mock_log.assert_called_once()

    def test_success_save_audit_log(self):
        body = {User.HEIGHT: 185}
        rsp = self.flask_client.post(
            f"{self.base_path}/{USER_ID}",
            json=body,
            headers=self.get_headers_for_token(USER_ID),
        )
        log = self.mongo_database[
            MongoAuditLogRepository.AUDIT_LOG_COLLECTION
        ].find_one({AuditLog.ACTION: AuthorizationAction.UpdateUser.value})
        self.assertIsNotNone(log)
        self.assertEqual(log[AuditLog.ACTION], AuthorizationAction.UpdateUser.value)
        self.assertEqual(log[AuditLog.REQUEST_OBJECT], body)
        self.assertEqual(log[AuditLog.RESPONSE_OBJECT], rsp.json)
        self.assertEqual(log[AuditLog.USER_ID], USER_ID)
        self.assertEqual(log[AuditLog.TARGET_ID], USER_ID)
        self.assertIsNotNone(log[AuditLog.CREATE_DATE_TIME])
