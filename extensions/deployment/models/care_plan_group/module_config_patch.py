"""Module Config Patch model"""
from enum import Enum
from typing import Optional

from jsonpatch import apply_patch

from extensions.common.exceptions import InvalidPatchChangeType
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.validators import validate_object_id
from extensions.module_result.models.module_config import ModuleConfig
from .patch import Patch


@convertibleclass
class ModuleConfigPatch:
    class ChangeType(Enum):
        REMOVE = "REMOVE"
        PATCH = "PATCH"

    MODULE_CONFIG_ID = "moduleConfigId"
    CHANGE_TYPE = "changeType"
    PATCH = "patch"

    moduleConfigId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    changeType: ChangeType = default_field()
    patch: list[Patch] = default_field()

    def apply_to(self, module_config) -> Optional[ModuleConfig]:

        if self.changeType == ModuleConfigPatch.ChangeType.PATCH:
            patches = [item.to_dict(include_none=False) for item in self.patch]
            module_config_dict = module_config.to_dict(include_none=False)
            apply_patch(module_config_dict, patches, in_place=True)
            return ModuleConfig.from_dict(module_config_dict)
        elif self.changeType == ModuleConfigPatch.ChangeType.REMOVE:
            # We dont append this moduleConfig because the ChangeType is "REMOVE"
            return None
        else:
            # Raise issue as we only have two ChangeTypes : "PATCH" and "REMOVE"
            raise InvalidPatchChangeType(self.changeType)
