from typing import Optional, Union

from flask import Blueprint
from flask_limiter import Limiter

from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.server_config import PhoenixServerConfig, StorageConfig
from sdk.storage.callbacks.binder import PostStorageSetupEvent
from sdk.storage.di.components import bind_storage_repository
from sdk.storage.repository.storage_repository import StorageRepository
from sdk.storage.router.storage_router import (
    api,
    api_v1,
    download_file_v1,
    retrieve_download_url_v1,
    upload_file,
    download_file,
    retrieve_download_url,
    upload_file_v1,
)


class StorageComponent(PhoenixBaseComponent):
    config_class = StorageConfig
    tag_name = "storage"

    def post_setup(self):
        pass

    @property
    def api_specs(self):
        return {
            "endpoint": f"apispec_{self.name.lower()}",
            "route": f"/apispec_{self.name.lower()}.json",
            "rule_filter": lambda rule: True
            if rule.rule.startswith("/api/storage/v1beta")
            else False,
            "model_filter": lambda tag: True,  # all in
        }

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return api

    @property
    def url_prefix(self):
        return f"/api/storage/v1beta"

    def setup_rate_limiter(self, limiter: Limiter):
        limiter_config = self.config.rateLimit
        if limiter_config and limiter_config.enable:
            # configure whole blueprint if default is present
            if limiter_config.default:
                limiter.limit(limiter_config.default)(self.blueprint)

            # routes to be configured by read parameter
            if limiter_config.read:
                for route in [download_file, retrieve_download_url]:
                    limiter.limit(limiter_config.read)(route)

            # routes to be configured by write parameter
            if limiter_config.write:
                limiter.limit(limiter_config.write)(upload_file)

    def setup_auth(self):
        super(StorageComponent, self).setup_auth()
        blueprint = self.blueprint

        @blueprint.before_request
        def _setup_authz():
            server_config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
            config = getattr(server_config.server, self.tag_name)
            if config.enableAuth and config.enableAuthz:
                event_bus = inject.instance(EventBusAdapter)
                event_bus.emit(PostStorageSetupEvent(), raise_error=True)


class StorageComponentV1(PhoenixBaseComponent):
    config_class = StorageConfig
    tag_name = "storage"

    def post_setup(self):
        self._create_indexes()

    @property
    def api_specs(self):
        return {
            "endpoint": f"apispec_{self.name.lower()}",
            "route": f"/apispec_{self.name.lower()}.json",
            "rule_filter": lambda rule: True
            if rule.rule.startswith("/api/storage/v1/")
            else False,
            "model_filter": lambda tag: True,
        }

    @property
    def blueprint(self) -> Optional[Union[Blueprint, list[Blueprint]]]:
        return api_v1

    @property
    def url_prefix(self):
        return f"/api/storage/v1"

    def bind(self, binder: inject.Binder, config: PhoenixServerConfig):
        bind_storage_repository(binder, config)

    def setup_rate_limiter(self, limiter: Limiter):
        limiter_config = self.config.rateLimit
        if limiter_config and limiter_config.enable:
            if limiter_config.default:
                limiter.limit(limiter_config.default)(self.blueprint)

            if limiter_config.read:
                for route in [download_file_v1, retrieve_download_url_v1]:
                    limiter.limit(limiter_config.read)(route)

            if limiter_config.write:
                limiter.limit(limiter_config.write)(upload_file_v1)

    @autoparams()
    def _create_indexes(self, repo: StorageRepository):
        repo.create_indexes()
