"""Care Plan Group model"""
from datetime import datetime
from typing import Optional

from extensions.common.exceptions import InvalidCarePlanGroupException
from sdk.common.utils.convertible import convertibleclass, meta, default_field
from sdk.common.utils.validators import (
    validate_object_id,
    validate_entity_name,
    default_datetime_meta,
)
from .group import Group


@convertibleclass
class CarePlanGroup:
    GROUPS = "groups"

    groups: list[Group] = default_field()

    def get_care_plan_group_by_id(
        self, group_id: str, raise_error=False
    ) -> Optional[Group]:
        if not group_id:
            return None
        groups = self.groups or []
        filtered_groups = (item for item in groups if item.id == group_id)
        care_plan_group = next(filtered_groups, None)
        if not care_plan_group and raise_error:
            raise InvalidCarePlanGroupException(group_id)
        return care_plan_group


@convertibleclass
class CarePlanGroupLog:
    ID = "_id"
    USER_ID = "userId"
    DEPLOYMENT_ID = "deploymentId"
    FROM_CARE_PLAN_GROUP_ID = "fromCarePlanGroupId"
    TO_CARE_PLAN_GROUP_ID = "toCarePlanGroupId"
    SUBMITTER_ID = "submitterId"
    SUBMITTER_NAME = "submitterName"
    NOTE = "note"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    userId: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    deploymentId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    fromCarePlanGroupId: str = default_field(metadata=meta(validate_entity_name))
    toCarePlanGroupId: str = default_field(metadata=meta(validate_entity_name))
    submitterId: str = default_field(
        metadata=meta(validate_object_id, value_to_field=str)
    )
    submitterName: str = default_field(metadata=meta(validate_entity_name))
    note: str = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())


class CarePlanGroupDeploymentExtension:
    carePlanGroup: CarePlanGroup = None
    moduleConfigs = None

    @property
    def care_plan_groups(self):
        if not (self.carePlanGroup and self.carePlanGroup.groups):
            return None

        return self.carePlanGroup.groups

    def validate_care_plan_group_id(self, care_plan_group_id: str):
        care_plan_group_exist = self.carePlanGroup.get_care_plan_group_by_id

        if not (self.carePlanGroup and care_plan_group_exist(care_plan_group_id)):
            raise InvalidCarePlanGroupException(care_plan_group_id)

    def retrieve_default_care_plan_group(self):
        groups = self.care_plan_groups
        if not groups:
            return None

        return next((group for group in groups if group.default), None)

    def retrieve_care_plan_group_by_code(self, extension_code: str) -> Optional[Group]:
        groups = self.care_plan_groups
        if not groups:
            return None

        filtered = (g for g in groups if extension_code == g.extensionForActivationCode)
        group = next(filtered, None)
        return group or self.retrieve_default_care_plan_group()

    def retrieve_care_plan_groups(self) -> dict:
        groups = self.care_plan_groups
        if not groups:
            return {}

        care_plan_group_dict = {}
        for group in groups:
            patched_module_configs = self.patch_module_configs_by_group(group)
            care_plan_group_dict[group.id] = {"moduleConfigs": patched_module_configs}
        return care_plan_group_dict

    def patch_module_configs_by_group(self, care_plan_group: Group) -> list:
        if not self.moduleConfigs:
            return []
        care_plan_group_dict = care_plan_group.valid_patches_dict()
        patched_module_configs = []
        for module_config in self.moduleConfigs or []:
            patch = care_plan_group_dict.get(module_config.id, None)
            if patch:
                patched_module_config = patch.apply_to(module_config)
                if patched_module_config:
                    patched_module_configs.append(patched_module_config)
            else:
                patched_module_configs.append(module_config)
        return patched_module_configs
