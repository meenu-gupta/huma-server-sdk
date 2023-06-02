import argparse
import logging
import os
import sys
import time

from dotenv import load_dotenv

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from extensions.appointment.component import AppointmentComponent
from extensions.authorization.component import AuthorizationComponent
from extensions.config.config import ExtensionServerConfig
from extensions.deployment.component import DeploymentComponent
from extensions.key_action.component import KeyActionComponent
from extensions.medication.component import MedicationComponent
from extensions.organization.component import OrganizationComponent
from extensions.reminder.component import UserModuleReminderComponent
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.calendar.tasks import prepare_events_for_next_day
from sdk.phoenix.component_manager import PhoenixComponentManager
from sdk.phoenix.server import PhoenixServer

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
        OrganizationComponent(),
        DeploymentComponent(),
        MedicationComponent(),
        UserModuleReminderComponent(),
        CalendarComponent(),
        KeyActionComponent(),
    ]

    component_manager = PhoenixComponentManager()
    component_manager.register_components(components)

    phoenix_server = PhoenixServer(
        config=phoenix_cfg,
        localization_path=loc_path,
        component_manager=component_manager,
    )

    log = logging.getLogger(__name__)

    s_time = time.time()
    log.info("+ prepare_events_for_next_day started")
    prepare_events_for_next_day()
    log.info(f"+ prepare_events_for_next_day ended after {time.time() - s_time}")
