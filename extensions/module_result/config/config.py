from dataclasses import field
from extensions.kardia.models.kardia_integration_config import KardiaIntegrationConfig
from extensions.module_result.config.cvd_integration import CVDIntegrationConfig
from extensions.module_result.config.pam_integration_client_config import (
    PAMIntegrationClientConfig,
)
from sdk import convertibleclass
from sdk.common.utils.convertible import default_field
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class ModuleResultConfig(BasePhoenixConfig):
    applyDefaultDisclaimerConfig: bool = field(default=True)
    pamIntegration: PAMIntegrationClientConfig = default_field()
    kardia: KardiaIntegrationConfig = default_field()
    cvd: CVDIntegrationConfig = default_field()
