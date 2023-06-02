"""Group model"""
from dataclasses import field

from extensions.common.exceptions import CarePlanGroupFieldMissingError
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from sdk.common.utils.validators import validate_care_plan_activation_code
from .module_config_patch import ModuleConfigPatch


@convertibleclass
class Group:
    ID = "id"
    NAME = "name"
    MODULE_CONFIG_PATCHES = "moduleConfigPatches"
    DEFAULT = "default"
    EXTENSION_FOR_ACTIVATION_CODE = "extensionForActivationCode"
    ORDER = "order"
    VALID_SORT_FIELDS = [ORDER]

    id: str = required_field()
    name: str = default_field()
    moduleConfigPatches: list[ModuleConfigPatch] = default_field()
    default: bool = field(default=False)
    extensionForActivationCode: str = default_field(
        metadata=meta(validate_care_plan_activation_code)
    )
    order: int = field(default=0)

    def valid_patches_dict(self) -> dict[str, ModuleConfigPatch]:
        """Builds a dict like {moduleConfigId: ModuleConfigPatch]}"""
        care_plan_group_dict = {}
        for patch in self.moduleConfigPatches:
            if patch.moduleConfigId:
                care_plan_group_dict[patch.moduleConfigId] = patch
            else:
                raise CarePlanGroupFieldMissingError(ModuleConfigPatch.MODULE_CONFIG_ID)
        return care_plan_group_dict
