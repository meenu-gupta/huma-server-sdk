import unittest
from pathlib import Path

from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.tests.test_case import SdkTestCase


class BaseCalendarTestCase(SdkTestCase):
    components = [AuthComponent(), CalendarComponent()]
    fixtures = [Path(__file__).parent.joinpath("fixtures/deployments_dump.json")]


class CalendarDebugTestCase(BaseCalendarTestCase):
    def test_render_route(self):
        rsp = self.flask_client.get("/api/calendar/v1beta/render/test")
        self.assertEqual(rsp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
