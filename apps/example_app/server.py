import argparse
import os
import sys

from dotenv import load_dotenv

here = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from apps.ppserver.version import (
    __VERSION__ as SERVER_VERSION,
    __API_VERSION__ as API_VERSION,
    __BUILD__ as BUILD,
)
from extensions.config.config import ExtensionServerConfig

from sdk.notification.component import NotificationComponent
from sdk.storage.callbacks.binder import PostStorageSetupEvent
from sdk.auth.component import AuthComponent
from sdk.phoenix.component_manager import PhoenixComponentManager
from sdk.storage.component import StorageComponent, StorageComponentV1
from sdk.phoenix.server import PhoenixServer
from sdk.versioning.component import VersionComponent

from extensions.authorization.component import AuthorizationComponent
from extensions.organization.component import OrganizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.module_result.modules.height_zscore import HeightZScoreModule

from extensions.authorization.callbacks import setup_storage_auth

from apps.example_app.modules.bmi.module import BMI2Module
from apps.example_app.modules.heartrate.module import HeartRate2Module

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
    override_mapping: dict[str, str] = dict(args.override_mapping or {})

    # setup config object to use in server and components
    phoenix_cfg = ExtensionServerConfig.get(conf_path, override_mapping)
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        StorageComponent(),
        StorageComponentV1(),
        OrganizationComponent(),
        DeploymentComponent(),
        ModuleResultComponent(
            additional_modules=[BMI2Module(), HeartRate2Module(), HeightZScoreModule()]
        ),
        NotificationComponent(),
        VersionComponent(
            server_version=SERVER_VERSION, api_version=API_VERSION, build=BUILD
        ),
    ]

    component_manager = PhoenixComponentManager()
    component_manager.register_components(components)

    phoenix_server = PhoenixServer(
        config=phoenix_cfg,
        component_manager=component_manager,
        server_version=SERVER_VERSION,
    )

    if args.run == SERVER:
        phoenix_server.event_bus.subscribe(PostStorageSetupEvent, setup_storage_auth)

        phoenix_server.listen_and_serve(prod=args.prod)

    elif args.run == WORKER:
        phoenix_server.run_worker()

    elif args.run == BEAT:
        phoenix_server.run_worker(beat=True)
