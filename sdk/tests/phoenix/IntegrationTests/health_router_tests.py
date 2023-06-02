from unittest.mock import patch

from pymongo.errors import AutoReconnect

from sdk.tests.test_case import SdkTestCase


class HealthRouterTests(SdkTestCase):
    components = []

    @classmethod
    def setUpClass(cls) -> None:
        super(HealthRouterTests, cls).setUpClass()

    @patch("sdk.phoenix.router.health_router.Database")
    def test_failure_inaccessible_db_live(self, db):
        db.command.side_effect = AutoReconnect()
        rsp = self.flask_client.get("/health/live")
        self.assertEqual(rsp.status_code, 400)
        self.assertEqual(rsp.data.decode("utf-8"), "Inaccessible database.")
