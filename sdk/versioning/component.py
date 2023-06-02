from typing import Optional, Union
from flask import Blueprint, Flask, request, g

from sdk.common.exceptions.exceptions import ClientUpdateRequiredException
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder, InjectorException
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.versioning.models.version import Version, VersionField
from sdk.versioning.router.version_router import version_blueprint
from sdk.versioning.user_agent_parser import UserAgent


class VersionComponent(PhoenixBaseComponent):
    tag_name = "version"

    def __init__(self, server_version: str, api_version: str, build: str = None):
        versions = {
            Version.API: api_version,
            Version.BUILD: build,
            Version.SERVER: VersionField(server_version),
        }
        self.version_dict = remove_none_values(versions)
        self.version = Version.from_dict(self.version_dict)

    @property
    def api_specs(self):
        return {
            "endpoint": f"apispec_{self.name.lower()}",
            "route": f"/apispec_{self.name.lower()}.json",
            "rule_filter": None,
            "model_filter": lambda tag: True,  # all in
        }

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return version_blueprint

    @property
    def enabled(self):
        return True

    def is_authz_enabled(self):
        return False

    def bind(self, binder: Binder, config: PhoenixServerConfig):
        binder.bind(Version, self.version)
        self.config = config

    def load_config(self, *args, **kwargs):
        return None, None

    def post_setup(self):
        self._inject_swagger_version()

    def _init_auth(self, blueprint: Blueprint):
        flask_app = inject.instance(Flask)

        @flask_app.before_request
        def _setup_auth():
            g.is_automation_request = "x-hu-api-automation-version" in request.headers
            request_agent = request.headers.get("x-hu-user-agent", None)

            if not request_agent:
                return

            user_agent = UserAgent.parse(request_agent)

            if not user_agent.client_type:
                return

            server_version = inject.instance(Version)

            if user_agent.version.major < server_version.server.major:
                raise ClientUpdateRequiredException

            client = self.config.server.project.get_client_by_client_type(
                user_agent.client_type
            )
            if client.minimumVersion and client.minimumVersion > user_agent.version:
                raise ClientUpdateRequiredException

            g.user_agent = user_agent

    def _inject_swagger_version(self):
        try:
            from flasgger import Swagger

            swagger = inject.instance(Swagger)
        except (ImportError, InjectorException):
            pass
        else:
            if not swagger.template:
                return
            if "info" in swagger.template:
                swagger.template["info"]["version"] = str(self.version.server)
            else:
                swagger.template["info"] = {"version": str(self.version.server)}
