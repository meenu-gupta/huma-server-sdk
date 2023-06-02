from typing import Optional, Union

from flask import Blueprint

from sdk.phoenix.component_manager import PhoenixBaseComponent
from sdk.phoenix.config.health_config import HealthConfig
from sdk.phoenix.router.health_router import api


class HealthComponent(PhoenixBaseComponent):
    config_class = HealthConfig
    tag_name = "health"

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
        return api

    def setup_auth(self):
        pass
