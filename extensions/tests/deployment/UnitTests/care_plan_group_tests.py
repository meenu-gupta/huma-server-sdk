from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.router.user_profile_request import (
    UpdateUserCarePlanGroupRequestObject,
)
from extensions.authorization.use_cases.update_care_plan_group_use_case import (
    UpdateUserCarePlanGroupUseCase,
)
from extensions.deployment.models.care_plan_group.care_plan_group import Group
from extensions.deployment.models.care_plan_group.module_config_patch import (
    ModuleConfigPatch,
)
from extensions.deployment.models.care_plan_group.patch import Patch
from extensions.deployment.router.deployment_requests import (
    CreateCarePlansRequestObject,
)
from extensions.module_result.models.module_config import ModuleConfig, ModuleSchedule
from sdk.common.utils.convertible import ConvertibleClassValidationError
from .test_helpers import (
    get_sample_care_plan_group,
    get_sample_update_care_plan_group_request_obj,
    get_sample_module_config,
    get_sample_module_config_patch,
    get_sample_module_config_with_rag_threshold,
    get_sample_module_config_patch_with_rag_threshold,
)


class MockAuthRepo:
    create_care_plan_group_log = MagicMock()
    retrieve_user = MagicMock()


class MockAuthService:
    retrieve_user_profile = MagicMock()
    update_user_profile = MagicMock()


class CreateCarePlanGroupTests(TestCase):
    def test_failure_request_object_with_no_groups(self):
        request_obj = get_sample_care_plan_group()
        request_obj.pop(CreateCarePlansRequestObject.GROUPS, None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateCarePlansRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_no_id(self):
        request_obj = get_sample_care_plan_group()
        request_obj[CreateCarePlansRequestObject.GROUPS][0].pop(Group.ID, None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateCarePlansRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_invalid_extension_activation_code(self):
        request_obj = get_sample_care_plan_group()
        request_obj[CreateCarePlansRequestObject.GROUPS][0][
            Group.EXTENSION_FOR_ACTIVATION_CODE
        ] = "123"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateCarePlansRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_two_default_true(self):
        request_obj = get_sample_care_plan_group()
        request_obj[CreateCarePlansRequestObject.GROUPS][1][Group.DEFAULT] = True
        with self.assertRaises(Exception):
            CreateCarePlansRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_invalid_patch_type(self):
        request_obj = get_sample_care_plan_group()
        request_obj[CreateCarePlansRequestObject.GROUPS][0][
            Group.MODULE_CONFIG_PATCHES
        ][0][ModuleConfigPatch.CHANGE_TYPE] = "DEL"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateCarePlansRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_invalid_patch_operation_type(self):
        request_obj = get_sample_care_plan_group()
        request_obj[CreateCarePlansRequestObject.GROUPS][0][
            Group.MODULE_CONFIG_PATCHES
        ][0][ModuleConfigPatch.PATCH][0][Patch.OP] = "DEL"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateCarePlansRequestObject.from_dict(request_obj)


class UpdateUserCarePlanGroupTests(TestCase):
    def test_failure_request_object_with_from_care_plan_group_id(self):
        request_obj = get_sample_update_care_plan_group_request_obj()
        request_obj["fromCarePlanGroupId"] = "com.huma.severe"
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateUserCarePlanGroupRequestObject.from_dict(request_obj)

    def test_failure_request_object_with_id(self):
        request_obj = get_sample_update_care_plan_group_request_obj()
        request_obj["id"] = "601bb29418c1ac7c73634737"
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateUserCarePlanGroupRequestObject.from_dict(request_obj)

    def test_success_request_object_to_user(self):
        request_obj = get_sample_update_care_plan_group_request_obj()
        update_request_obj = UpdateUserCarePlanGroupRequestObject.from_dict(request_obj)
        self.assertEqual(
            update_request_obj.to_user().carePlanGroupId,
            request_obj.get(UpdateUserCarePlanGroupRequestObject.CARE_PLAN_GROUP_ID),
        )

    def test_success_request_object_to_care_plan_group_log(self):
        request_obj = get_sample_update_care_plan_group_request_obj()
        care_plan_group_log = UpdateUserCarePlanGroupRequestObject.from_dict(
            request_obj
        ).to_care_plan_group_log()

        self.assertEqual(
            care_plan_group_log.toCarePlanGroupId,
            request_obj.get(UpdateUserCarePlanGroupRequestObject.CARE_PLAN_GROUP_ID),
        )

    @patch(
        f"extensions.authorization.use_cases.update_care_plan_group_use_case.AuthorizationService",
        MockAuthService,
    )
    def test_success_update_user_care_plan_group(self):
        request_obj = UpdateUserCarePlanGroupRequestObject.from_dict(
            get_sample_update_care_plan_group_request_obj()
        )
        use_case = UpdateUserCarePlanGroupUseCase(MockAuthRepo())
        use_case.validate_care_plan_group_id = MagicMock()
        use_case.send_care_plan_group_update_notifications = MagicMock()
        use_case.execute(request_obj)
        use_case.validate_care_plan_group_id.assert_called_once()
        use_case.send_care_plan_group_update_notifications.assert_called_once()
        MockAuthRepo().create_care_plan_group_log.assert_called_once()


class ModuleConfigPatchTests(TestCase):
    def test_failure_create_module_config_patch(self):
        request_obj = get_sample_module_config_patch()
        request_obj[ModuleConfigPatch.CHANGE_TYPE] = "CH"
        with self.assertRaises(ConvertibleClassValidationError):
            ModuleConfigPatch.from_dict(request_obj)

    def test_success_module_config_patch_apply_to(self):
        module_config = ModuleConfig.from_dict(get_sample_module_config())
        module_config_patch = ModuleConfigPatch.from_dict(
            get_sample_module_config_patch()
        )
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual("P4D", patched_module_config.schedule.isoDuration)

        module_config_patch.changeType = ModuleConfigPatch.ChangeType.REMOVE
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertIsNone(patched_module_config)

    def test_success_module_config_patch_apply_to_with_string_times_per_duration_value_replace(
        self,
    ):
        module_config = ModuleConfig.from_dict(get_sample_module_config())
        mc_patch = get_sample_module_config_patch()
        mc_patch[ModuleConfigPatch.PATCH].append(
            {"op": "replace", "path": "/schedule/timesPerDuration", "value": "4"}
        )
        module_config_patch = ModuleConfigPatch.from_dict(mc_patch)
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual(4, patched_module_config.schedule.timesPerDuration)

    def test_success_module_config_patch_apply_to_with_string_times_per_duration_value(
        self,
    ):
        mc_dict = get_sample_module_config()
        mc_dict[ModuleConfig.SCHEDULE].pop(ModuleSchedule.TIMES_PER_DURATION)
        module_config = ModuleConfig.from_dict(get_sample_module_config())
        mc_patch = get_sample_module_config_patch()
        mc_patch[ModuleConfigPatch.PATCH].append(
            {"op": "add", "path": "/schedule/timesPerDuration", "value": "4"}
        )
        module_config_patch = ModuleConfigPatch.from_dict(mc_patch)
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual(4, patched_module_config.schedule.timesPerDuration)

    def test_success_module_config_patch_apply_to_with_string_order_value(self):
        module_config = ModuleConfig.from_dict(get_sample_module_config())
        mc_patch = get_sample_module_config_patch()
        mc_patch[ModuleConfigPatch.PATCH].append(
            {"op": "replace", "path": "/order", "value": "3"}
        )
        module_config_patch = ModuleConfigPatch.from_dict(mc_patch)
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual(3, patched_module_config.order)

    def test_success_module_config_patch_apply_to_with_string_version_value(self):
        module_config = ModuleConfig.from_dict(get_sample_module_config())
        mc_patch = get_sample_module_config_patch()
        mc_patch[ModuleConfigPatch.PATCH].append(
            {"op": "replace", "path": "/version", "value": "2"}
        )
        module_config_patch = ModuleConfigPatch.from_dict(mc_patch)
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual(2, patched_module_config.version)

    def test_success_module_config_patch_apply_to_with_string_severity_value(self):
        module_config = ModuleConfig.from_dict(
            get_sample_module_config_with_rag_threshold()
        )
        mc_patch = get_sample_module_config_patch_with_rag_threshold()
        module_config_patch = ModuleConfigPatch.from_dict(mc_patch)
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual(1, patched_module_config.ragThresholds[0].severity)

    def test_success_module_config_patch_apply_to_with_string_threshold_range_values(
        self,
    ):
        module_config = ModuleConfig.from_dict(
            get_sample_module_config_with_rag_threshold()
        )
        mc_patch = get_sample_module_config_patch_with_rag_threshold()

        max_value = 122.3
        min_value = 11.44
        mc_patch[ModuleConfigPatch.PATCH] += [
            {
                "op": "replace",
                "path": "/ragThresholds/0/thresholdRange/0/maxValue",
                "value": str(max_value),
            },
            {
                "op": "replace",
                "path": "/ragThresholds/0/thresholdRange/0/minValue",
                "value": str(min_value),
            },
        ]
        module_config_patch = ModuleConfigPatch.from_dict(mc_patch)
        patched_module_config = module_config_patch.apply_to(module_config)
        self.assertEqual(
            max_value, patched_module_config.ragThresholds[0].thresholdRange[0].maxValue
        )
        self.assertEqual(
            min_value, patched_module_config.ragThresholds[0].thresholdRange[0].minValue
        )
