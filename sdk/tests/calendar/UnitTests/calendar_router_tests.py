import unittest
from unittest.mock import patch

from flask import Flask

from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.router.calendar_router import export_calendar

CALENDAR_ROUTER_PATH = "sdk.calendar.router.calendar_router"
SAMPLE_ID = "600a8476a961574fb38157d5"

testapp = Flask(__name__)
testapp.app_context().push()


class CalendarRouterTestCase(unittest.TestCase):
    @patch(f"{CALENDAR_ROUTER_PATH}.BytesIO")
    @patch(f"{CALENDAR_ROUTER_PATH}.send_file")
    @patch(f"{CALENDAR_ROUTER_PATH}.pytz")
    @patch(f"{CALENDAR_ROUTER_PATH}.CalendarService")
    @patch(f"{CALENDAR_ROUTER_PATH}.ExportCalendarRequestObject")
    def test_success_export_calendar(self, req_obj, service, pytz, send_file, BytesIO):
        user_id = SAMPLE_ID
        with testapp.test_request_context("/", method="GET") as _:
            export_calendar(user_id)
            req_obj.from_dict.assert_called_with({CalendarEvent.USER_ID: user_id})
            service().export_calendar.assert_called_with(
                start=req_obj.from_dict().start,
                end=req_obj.from_dict().end,
                timezone=pytz.timezone(),
                userId=req_obj.from_dict().userId,
                debug=req_obj.from_dict().debug,
            )
            send_file.assert_called_with(
                BytesIO(),
                attachment_filename="calendar_export.ics",
                as_attachment=True,
                mimetype="text/ics",
            )


if __name__ == "__main__":
    unittest.main()
