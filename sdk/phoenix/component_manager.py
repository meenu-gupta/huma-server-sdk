import logging
from abc import ABC, abstractmethod
from typing import Optional, Union

from flask import Blueprint, Flask
from flask_limiter import Limiter

from sdk.auth.decorators import check_auth
from sdk.common.logging.middleware import RequestErrorHandlerMiddleware
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder
from sdk.phoenix.config.server_config import BasePhoenixConfig, PhoenixServerConfig

logger = logging.getLogger(__name__)


class PhoenixComponent(ABC):
    component_type: str = "extensions"
    QUEUE = "queue"
    config: Optional[BasePhoenixConfig] = None
    config_class: type = None
    routers: list[Blueprint] = []
    tag_name = None
    tasks: list[str] = []
    dedicated_task_queues: dict[str, dict[str, str]] = {}
    _ignored_error_codes = ()
    _warn_error_codes = ()

    @abstractmethod
    def api_specs(self):
        raise NotImplementedError

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return self.routers

    @abstractmethod
    def bind(self, binder: Binder, config: PhoenixServerConfig):
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def setup_rate_limiter(self, limiter: Limiter):
        raise NotImplementedError

    @abstractmethod
    def load_config(self, config: PhoenixServerConfig) -> tuple[BasePhoenixConfig, str]:
        raise NotImplementedError

    @property
    def auth_enabled(self):
        return self.config and self.config.enableAuth

    @property
    def enabled(self):
        return self.config and self.config.enable

    @property
    def url_prefix(self):
        return f"/api/{self.component_type}/v1beta/{self.tag_name}"

    def include_config(self, server_config: PhoenixServerConfig):
        if not (self.config_class and self.tag_name):
            raise Exception("Config class and tag name should be provided.")
        if server_config.server:
            self.config = getattr(
                server_config.server, self.tag_name, self.config_class()
            )

    def pre_setup(self):
        pass

    def post_setup(self):
        pass

    def setup_auth(self):
        if isinstance(self.blueprint, list):
            for bp in self.blueprint:
                self._init_auth(bp)
        else:
            self._init_auth(self.blueprint)

    def _init_auth(self, blueprint: Blueprint):
        @blueprint.before_request
        def _setup_auth():
            self.default_auth()

    def default_auth(self):
        server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
        config = getattr(server_config.server, self.tag_name)
        if not config.enableAuth:
            return
        check_auth()

    def _register_ignored_error_codes(self):
        for code in self._ignored_error_codes:
            RequestErrorHandlerMiddleware.ignore_error_code(code)

    def _register_warn_error_codes(self):
        for code in self._warn_error_codes:
            RequestErrorHandlerMiddleware.warn_error_code(code)


class PhoenixBaseComponent(PhoenixComponent):
    def setup_rate_limiter(self, limiter: Limiter) -> Optional[type]:
        return None

    def load_config(self, config: PhoenixServerConfig) -> tuple[BasePhoenixConfig, str]:
        self.include_config(config)
        return self.config, self.tag_name

    # default component binder
    def bind(self, binder: Binder, config: PhoenixServerConfig):
        return True

    def is_authz_enabled(self):
        server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
        config = getattr(server_config.server, self.tag_name)
        if not config.enableAuth or not config.enableAuthz:
            return False
        return True

    def post_setup(self):
        blueprints = [self.blueprint]
        if isinstance(self.blueprint, (list, tuple)):
            blueprints = self.blueprint

        authz_enabled = self.is_authz_enabled()
        for blueprint in blueprints:
            if hasattr(blueprint, "policy_enabled"):
                blueprint.policy_enabled = authz_enabled

        self._register_ignored_error_codes()
        self._register_warn_error_codes()

    @property
    def name(self) -> str:
        """
        Return class name without Component as name property.
        ex. c = FooComponent -> Foo
        """
        return self.__class__.__name__.replace("Component", "")

    @property
    def api_specs(self):
        return None


class PhoenixComponentManager:
    class SetupContextManager:
        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exit_callback()

    def __init__(self):
        self._registered_components: list[PhoenixComponent] = []

    def register_components(self, components: list[PhoenixComponent]):
        self._registered_components.extend(components)

    def setup_blueprints_and_limiting(self, rate_limiter):
        flask_app = inject.instance(Flask)
        for component in self.components:
            if component.enabled:
                component.setup_rate_limiter(rate_limiter)
                logger.debug(f"{component.name} rate limiter has been configured")
                if component.blueprint:
                    component.setup_auth()
                    if isinstance(component.blueprint, list):
                        for route in component.blueprint:
                            flask_app.register_blueprint(route)
                    else:
                        flask_app.register_blueprint(component.blueprint)
                logger.debug(f"{component.name} routers has been configured")
            else:
                logger.debug(f"{component.name} routers has been disabled and skipped")

    def reset(self):
        self._registered_components.clear()

    def setup(self, config: PhoenixServerConfig):
        self.filter_enabled_components(config)
        self.pre_setup_and_load_config(config)
        return self.SetupContextManager(self.post_setup)

    def filter_enabled_components(self, phoenix_config: PhoenixServerConfig):
        enabled_components = []
        for component in self.components:
            component.load_config(phoenix_config)
            if component.enabled:
                enabled_components.append(component)

        self.reset()
        self.register_components(enabled_components)

    def pre_setup_and_load_config(self, phoenix_config: PhoenixServerConfig):
        for component in self.components:
            component.pre_setup()
            config, tag = component.load_config(phoenix_config)
            if config and tag:
                setattr(phoenix_config.server, tag, config)

    @property
    def components(self) -> list[PhoenixComponent]:
        return self._registered_components

    @property
    def api_specs(self) -> list[dict]:
        return [
            component.api_specs
            for component in self._registered_components
            if component.api_specs
        ]

    def component(self, name: str) -> Optional[PhoenixComponent]:
        try:
            return next(
                filter(lambda x: x.tag_name == name, self._registered_components)
            )
        except StopIteration:
            raise Exception("Component with such name doesn't exist.")

    def post_setup(self):
        for component in self.components:
            component.post_setup()
