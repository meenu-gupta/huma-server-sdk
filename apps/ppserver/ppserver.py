import argparse
import os
import sys

from dotenv import load_dotenv

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from apps.ppserver.callbacks.inbox_auth import (
    setup_inbox_send_auth,
    setup_inbox_search_auth,
    setup_inbox_confirm_auth,
)
from apps.ppserver.version import (
    __VERSION__ as SERVER_VERSION,
    __API_VERSION__ as API_VERSION,
    __BUILD__ as BUILD,
)
from apps.ppserver.components.auth_helper.router import helper_router
from extensions.appointment.component import AppointmentComponent
from extensions.authorization.callbacks import setup_storage_auth
from extensions.authorization.component import AuthorizationComponent
from extensions.autocomplete.component import AutocompleteComponent
from extensions.config.config import ExtensionServerConfig
from extensions.deployment.component import DeploymentComponent
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.identity_verification.component import IdentityVerificationComponent
from extensions.kardia.component import KardiaComponent
from extensions.key_action.component import KeyActionComponent
from extensions.medication.component import MedicationComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.modules.height_zscore import HeightZScoreModule
from extensions.organization.component import OrganizationComponent
from extensions.publisher.component import PublisherComponent
from extensions.reminder.component import UserModuleReminderComponent
from extensions.revere.component import RevereComponent
from extensions.twilio_video.component import TwilioVideoComponent
from extensions.dashboard.component import DashboardComponent
from sdk.audit_logger.component import AuditLoggerComponent
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.utils.flask_request_utils import PhoenixJsonEncoder
from sdk.inbox.component import InboxComponent
from sdk.inbox.events.auth_events import (
    InboxSearchAuthEvent,
    InboxSendAuthEvent,
    InboxConfirmAuthEvent,
)
from sdk.notification.component import NotificationComponent
from sdk.phoenix.component_manager import PhoenixComponentManager
from sdk.phoenix.server import PhoenixServer
from sdk.storage.callbacks.binder import PostStorageSetupEvent
from sdk.storage.component import StorageComponent, StorageComponentV1
from sdk.versioning.component import VersionComponent

SERVER = "server"
WORKER = "worker"
BEAT = "beat"
RUN_CHOICES = [SERVER, WORKER, BEAT]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="auth app cli.")
    parser.add_argument(
        "--config", type=str, help="yaml config path", default="config.dev.yaml"
    )
    parser.add_argument(
        "--dotenv", type=str, help="dotenv file path", default="dev.env"
    )
    parser.add_argument(
        "--prod", type=bool, help="enable wsgi for production mode", default=False
    )
    parser.add_argument(
        "--run",
        type=str,
        help=f"Type of app to run. Choices: {RUN_CHOICES}",
        default=SERVER,
    )
    parser.add_argument(
        "--set",
        action="append",
        type=lambda kv: kv.split("="),
        help="Argument which should be overridden in config."
        " Example: --set server.authorization.enable=false --set server.deployment.enable=false",
        default=None,
        dest="override_mapping",
    )
    args = parser.parse_args()

    # get dotenv path and load
    dotenv_path = os.path.join(here, args.dotenv)
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    conf_path = os.path.join(here, args.config)
    loc_path = os.path.join(here, "localization")
    override_mapping: dict[str, str] = dict(args.override_mapping or {})

    # setup config object to use in server and components
    phoenix_cfg = ExtensionServerConfig.get(conf_path, override_mapping)
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        AppointmentComponent(),
        StorageComponent(),
        StorageComponentV1(),
        OrganizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(additional_modules=[HeightZScoreModule()]),
        MedicationComponent(),
        UserModuleReminderComponent(),
        CalendarComponent(),
        InboxComponent(),
        RevereComponent(),
        NotificationComponent(),
        TwilioVideoComponent(),
        KeyActionComponent(),
        KardiaComponent(),
        ExportDeploymentComponent(),
        VersionComponent(
            server_version=SERVER_VERSION,
            api_version=API_VERSION,
            build=BUILD,
        ),
        IdentityVerificationComponent(),
        AutocompleteComponent(),
        PublisherComponent(),
        AuditLoggerComponent(),
        DashboardComponent(),
    ]

    component_manager = PhoenixComponentManager()
    component_manager.register_components(components)

    phoenix_server = PhoenixServer(
        config=phoenix_cfg,
        localization_path=loc_path,
        component_manager=component_manager,
        server_version=SERVER_VERSION,
        encoder=PhoenixJsonEncoder,
    )

    if args.run == SERVER:
        config = phoenix_server.config.server
        if config.debugRouter:
            app = phoenix_server.flask_app
            app.secret_key = config.adapters.jwtToken.secret
            app.register_blueprint(helper_router)
        phoenix_server.event_bus.subscribe(PostStorageSetupEvent, setup_storage_auth)
        phoenix_server.event_bus.subscribe(InboxSendAuthEvent, setup_inbox_send_auth)
        phoenix_server.event_bus.subscribe(
            InboxConfirmAuthEvent, setup_inbox_confirm_auth
        )
        phoenix_server.event_bus.subscribe(
            InboxSearchAuthEvent, setup_inbox_search_auth
        )

        phoenix_server.listen_and_serve(prod=args.prod)

    elif args.run == WORKER:
        phoenix_server.run_worker()

    elif args.run == BEAT:
        phoenix_server.run_worker(beat=True)
