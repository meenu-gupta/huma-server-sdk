from flask import request, g

from sdk.auth.decorators import check_auth
from sdk.calendar.di.components import bind_calendar_repository
from sdk.calendar.router.calendar_router import calendar_route
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig, CalendarConfig


class CalendarComponent(PhoenixBaseComponent):
    config_class = CalendarConfig
    component_type = "sdk"
    tag_name = "calendar"
    tasks = ["sdk.calendar"]
    dedicated_task_queues = {
        "sdk.calendar.tasks.*": {PhoenixBaseComponent.QUEUE: "notification"}
    }

    def __init__(self):
        self.routers = [calendar_route]

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_calendar_repository(binder, config)

    def setup_auth(self):
        blueprint = self.blueprint[0]

        @blueprint.before_request
        def _setup_authz():
            server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
            config = getattr(server_config.server, self.tag_name)

            # TODO: find a solution if this will be used later
            if server_config.server.debugRouter:
                return

            if not config.enableAuth:
                return
            check_auth()
            if not config.enableAuthz:
                return

            action = "READ" if request.method == "GET" else "WRITE"
            user_id = request.view_args.get("user_id", None)
            self.check_permission(g.user.id, f"user_data:{user_id}", action)
