import json
import logging
from typing import Type

from celery import Celery
from celery.utils import instantiate
from flask import Flask
from flask_limiter import Limiter
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.middleware.proxy_fix import ProxyFix

from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.localization.utils import setup_i18n
from sdk.common.logging.setup import init_logging
from sdk.common.utils import inject
from sdk.common.utils.flask_request_utils import private_ip_required
from sdk.phoenix.component import HealthComponent
from sdk.phoenix.component_manager import PhoenixComponentManager
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.phoenix.di.components import setup_di


class PhoenixServer:
    default_components = [HealthComponent()]

    def __init__(
        self,
        config: PhoenixServerConfig,
        localization_path: str = None,
        component_manager: PhoenixComponentManager = None,
        testing: bool = False,
        server_version: str = None,
        encoder: Type[json.JSONEncoder] = None,
    ):
        self.config = config
        self.logger = self.init_logging()
        self.localization_path = localization_path
        self.component_manager = component_manager or PhoenixComponentManager()
        self.configure(testing, server_version)
        self.encoder = encoder

    @property
    def flask_app(self) -> Flask:
        return inject.instance(Flask)

    @property
    def rate_limiter(self) -> Limiter:
        return inject.instance(Limiter)

    @property
    def event_bus(self):
        return inject.instance(EventBusAdapter)

    def configure(self, testing: bool, server_version: str):
        self.setup_i18n()

        self.component_manager.register_components(self.default_components)
        with self.component_manager.setup(self.config):
            setup_di(
                self.config,
                self.component_manager,
                self._api_specs(),
                clear=testing,
                server_version=server_version,
                localization_path=self.localization_path,
            )
            self.component_manager.setup_blueprints_and_limiting(self.rate_limiter)

        PrometheusMetrics(self.flask_app, metrics_decorator=private_ip_required)

    def init_logging(self):
        init_logging(debug=self.config.server.debugLog)
        return logging.getLogger(__name__)

    def setup_i18n(self):
        if self.localization_path:
            setup_i18n(self.localization_path)

    def listen_and_serve(self, prod=False):
        conf = self.config
        app = self.flask_app
        if self.encoder:
            app.json_encoder = self.encoder

        if prod:
            from waitress import serve

            app.wsgi_app = ProxyFix(app.wsgi_app)
            serve(
                app,
                host=conf.server.host,
                port=conf.server.port,
                _quiet=conf.server.debug,
            )
        else:
            app.run(conf.server.host, conf.server.port, conf.server.debug)

    def _api_specs(self):
        specs = self.component_manager.api_specs
        sdk_spec = {
            "endpoint": f'apispec_{"sdk".lower()}',
            "route": f'/apispec_{"sdk".lower()}.json',
            "rule_filter": lambda rule: True
            if rule.rule.startswith("/api/auth/v1beta")
            or rule.rule.startswith("/api/storage/v1beta")
            else False,
            "model_filter": lambda tag: True,  # all in
        }
        specs.append(sdk_spec)
        return specs

    def run_worker(self, beat=False):
        celery_app = inject.instance(Celery)
        if beat:
            self._run_beat(celery_app)
        else:
            self._run_worker(celery_app)

    def _run_worker(self, celery_app: Celery):

        cli_args = f"--concurrency=8 --pool=threads"
        task_routes: dict[str, dict[str, str]] = celery_app.conf.task_routes
        queues = [task["queue"] for task in task_routes.values()]
        if queues:
            queues.append("celery")
            queue_str = ",".join(queues)
            cli_args = f"{cli_args} --queues={queue_str}"
        celery_app.worker_main(cli_args.split())

    def _run_beat(self, celery_app: Celery):
        cli_args = "--scheduler=redbeat.RedBeatScheduler"
        beat_instance = instantiate("celery.bin.beat:beat", app=celery_app)
        beat_instance.execute_from_commandline(cli_args.split())
