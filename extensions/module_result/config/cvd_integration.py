from sdk.common.utils.convertible import meta, convertibleclass, required_field
from sdk.common.utils.validators import validate_entity_name, validate_url
from sdk.phoenix.config.server_config import BasePhoenixConfig


@convertibleclass
class CVDIntegrationConfig(BasePhoenixConfig):
    url: str = required_field(metadata=meta(validate_url))
    username: str = required_field(metadata=meta(validate_entity_name))
    password: str = required_field(metadata=meta(validate_entity_name))
