import logging
import pytz

from io import BytesIO

from flask import Blueprint, send_file, request, render_template

from sdk.calendar.events import CalendarViewUserDataEvent
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.calendar.models.calendar_view_user_data import CalendarViewUsersData
from sdk.calendar.router.calendar_request import ExportCalendarRequestObject
from sdk.calendar.service.calendar_service import CalendarService
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject

logger = logging.getLogger(__name__)

calendar_route = Blueprint(
    "calendar_route",
    __name__,
    url_prefix="/api/calendar/v1beta",
    template_folder="test_client_app/templates/",
    static_folder="test_client_app/static/",
)


@calendar_route.route("/user/<user_id>/export", methods=["GET"])
def export_calendar(user_id):
    body = dict(request.args) or {}
    body.update({CalendarEvent.USER_ID: user_id})
    logger.debug(f"Calendar Export for {user_id}: {body}")
    req: ExportCalendarRequestObject = ExportCalendarRequestObject.from_dict(body)

    data = CalendarService().export_calendar(
        start=req.start,
        end=req.end,
        timezone=pytz.timezone(req.timezone),
        userId=req.userId,
        debug=req.debug,
    )
    return send_file(
        BytesIO("".join([row for row in data]).encode()),
        attachment_filename="calendar_export.ics",
        as_attachment=True,
        mimetype="text/ics",
    )


@calendar_route.route("/render/test", methods=["GET"])
def test_calendar():
    event_bus = inject.instance(EventBusAdapter)
    event = CalendarViewUserDataEvent()
    data: list[CalendarViewUsersData] = event_bus.emit(event)

    if data:
        data = data[0]
    else:
        data = CalendarViewUsersData({}, [])

    return render_template("index.html", data=data)
