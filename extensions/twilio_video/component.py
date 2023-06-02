import logging
from typing import Optional, Union

from flask import Blueprint, request

from extensions.twilio_video.callbacks.callbacks import on_user_delete_callback
from extensions.twilio_video.config.config import TwilioVideoConfig
from extensions.twilio_video.di.components import bind_twilio_video_repository
from extensions.twilio_video.router.twilio_video_router import api, public_api
from sdk.auth.events.delete_user_event import DeleteUserEvent
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder, autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class TwilioVideoComponent(PhoenixBaseComponent):
    config_class = TwilioVideoConfig
    tag_name = "twilioVideo"

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        bind_twilio_video_repository(binder, config)

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return [api, public_api]

    def _init_auth(self, blueprint: Blueprint):
        if blueprint is public_api:
            return

        @blueprint.before_request
        def _setup_auth():
            # removing auth check for specified requests
            callbacks_request = request.path.endswith("/video/callbacks")
            static_request = "/static/" in request.path
            video_test_request = request.path.endswith("/video/test")
            if callbacks_request or static_request or video_test_request:
                return
            self.default_auth()

    @autoparams()
    def post_setup(self, event_bus: EventBusAdapter):
        server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
        host_url = getattr(server_config.server, "hostUrl", None)
        event_bus.subscribe(DeleteUserEvent, on_user_delete_callback)

        if not host_url:
            raise Exception('Twilio Component requires "hostUrl" to be configured')
        super().post_setup()
