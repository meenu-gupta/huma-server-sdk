from abc import ABC
from contextlib import contextmanager
from dataclasses import fields
from datetime import datetime
from typing import Iterator, Optional, Union, Type

from jsonschema import validate

from extensions.authorization.models.user import User, UnseenFlags
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.status import EnableStatus
from extensions.module_result.exceptions import (
    InvalidModuleConfiguration,
    InvalidModuleResultException,
)
from extensions.module_result.models.module_config import (
    CustomRagThreshold,
    RagThreshold,
    RagThresholdType,
    ThresholdRange,
    ModuleConfig,
)
from extensions.module_result.models.primitives import ChangeDirection
from extensions.module_result.models.primitives import Primitive, GroupCategory
from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    InvalidModuleConfigBody,
)
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import must_not_be_present


class Module(ABC):
    moduleId: str = None
    primitives: list[Type[Primitive]] = []
    recent_results_number = 2
    preferredUnitEnabled: bool = False
    usesListStringTranslation: bool = True
    _config: Optional[ModuleConfig] = None
    ragEnabled: bool = False
    visualizer = None

    @property
    def config(self) -> ModuleConfig:
        if not self._config:
            raise RuntimeError("Module is not configured with module config")
        return self._config

    @config.setter
    def config(self, config: ModuleConfig):
        if config is not None and not isinstance(config, ModuleConfig):
            raise RuntimeError(f"Module can not be configured with {type(config)}")
        self._config = config

    @contextmanager
    def configure(self, config: ModuleConfig):
        """
        A helper method to clear configuration after module is not needed.
        replaces this behavior
        module.config = module_config
        ...do something...
        module.config = None
        """
        self.config = config
        try:
            yield self
        finally:
            self._config = None

    @property
    def name(self):
        return type(self).__name__

    def get_visualizer(self, **kwargs):
        if not self.visualizer:
            raise RuntimeError(f"Visualizer for module {self.moduleId} is not defined")
        if not callable(self.visualizer):
            raise RuntimeError(f"Visualizer for module {self.moduleId} is not callable")
        return self.visualizer(self, **kwargs)

    def get_validation_schema(self) -> Optional[dict]:
        return

    def extract_module_config(
        self,
        module_configs: list[ModuleConfig],
        primitive: Optional[Primitive],
        module_config_id: str = None,
    ):
        """
        Extracts module config id from moduleConfigs by moduleId.
        Returns matched moduleConfig.
        Overwrite self.find_config method to change filter rule.
        """
        # extract moduleConfig by id if moduleConfigId is present
        if not module_config_id and primitive:
            module_config_id = primitive.moduleConfigId

        if module_config_id:
            module_config = find(
                lambda x: self._mc_filter_rule(x, module_config_id), module_configs
            )
            if module_config:
                return module_config
        else:
            # extract moduleConfig by moduleId or questionnaireId
            matched_configs = filter(self._mc_filter_rule, module_configs)
            module_config = self.find_config(matched_configs, primitive)
            if module_config:
                return module_config

        raise InvalidModuleConfiguration(
            message=f"{self.moduleId} with module config id {module_config_id} is not configured in module configs."
        )

    def find_config(
        self, matched_configs: Iterator[ModuleConfig], primitive: Primitive = None
    ) -> ModuleConfig:
        return find(lambda mc: mc.moduleId == self.moduleId, matched_configs)

    def filter_results(
        self,
        primitives: list[Primitive],
        module_configs: list[ModuleConfig],
        is_for_user=False,
    ) -> list[Primitive]:
        module_config_ids = {mc.id for mc in module_configs}
        return [item for item in primitives if item.moduleConfigId in module_config_ids]

    def calculate(self, primitive: Primitive):
        pass

    def preprocess(self, primitives: list[Primitive], user: User):
        for primitive in primitives:
            primitive.create_server_field()

    def to_dict(self) -> dict:
        return {
            "moduleId": self.moduleId,
            "primitiveIds": [type(item).__name__ for item in self.primitives],
        }

    def get_threshold_data(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive] = None,
    ) -> dict:
        threshold_data = {}
        threshold = self.calculate_threshold(
            target_primitive, module_config, primitives
        )
        if threshold:
            for key, value in threshold.items():
                threshold_data[key] = {}
                if value and value.color:
                    change_direction = self.calculate_change_direction(
                        target_primitive, primitives, value.fieldName
                    )
                    self._update_threshold_data(
                        threshold_data[key], value, change_direction, module_config
                    )

        return threshold_data

    def _update_threshold_data(
        self,
        threshold_data: dict,
        threshold: Union[RagThreshold, CustomRagThreshold],
        change_direction,
        module_config: ModuleConfig,
    ):
        threshold_data.update(
            {
                RagThreshold.COLOR: threshold.color,
                RagThreshold.SEVERITY: threshold.severity,
            }
        )
        if change_direction:
            threshold_data.update({RagThreshold.DIRECTION: change_direction})
        threshold_data[CustomRagThreshold.IS_CUSTOM] = self._is_custom_rag_config(
            module_config
        )

    def calculate_threshold(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive],
    ) -> Optional[dict]:
        """
        Calculate threshold for primitive by comparing it's value to previous.
        """
        # skip if no thresholds present
        if not module_config.ragThresholds:
            return

        threshold = {}
        for rag in module_config.ragThresholds:
            if not hasattr(target_primitive, rag.fieldName):
                continue

            if not rag.enabled:
                continue

            threshold_by_field_name = threshold.get(rag.fieldName)
            if not threshold_by_field_name:
                threshold[rag.fieldName] = None

            # skip if severity is lower than current
            if (
                threshold_by_field_name
                and rag.severity < threshold_by_field_name.severity
            ):
                continue

            # get value from primitive by fieldName
            value = getattr(target_primitive, rag.fieldName)
            avg_value = value

            if rag.type != RagThresholdType.VALUE:
                # skip if values to compare required but not provided
                if primitives:
                    values = [
                        getattr(primitive, rag.fieldName) or 0
                        for primitive in primitives
                    ]
                    avg_value = sum(values) / len(values)

                else:
                    continue

            calc_value = self._calculate_value(rag.type, value, avg_value)
            if calc_value is None:
                continue

            for threshold_range in rag.thresholdRange:
                # check if value matches current threshold
                if self._match_threshold(threshold_range, calc_value):
                    threshold[rag.fieldName] = rag
                    break

        return threshold

    def calculate_change_direction(
        self, new_primitive: Primitive, primitives: list[Primitive], field_name: str
    ) -> Optional[ChangeDirection]:
        """Calculate what direction value has changed in (INCREASED, DECREASED, NOCHANGE)"""
        change_direction = None
        if not primitives:
            return

        new_value = getattr(new_primitive, field_name)
        if not isinstance(new_value, (int, float)):
            return

        values = self._get_primitives_old_values(primitives, field_name)
        if not values:
            return ChangeDirection.NOCHANGE.value

        previous_value = sum(values) / len(values)

        # can't compare result if value is not float or int
        if isinstance(new_value, float) or isinstance(new_value, int):
            if new_value < previous_value:
                change_direction = ChangeDirection.DECREASED
            elif new_value > previous_value:
                change_direction = ChangeDirection.INCREASED
            else:
                change_direction = ChangeDirection.NOCHANGE
        return change_direction.value

    @staticmethod
    def _is_custom_rag_config(module_config: ModuleConfig) -> bool:
        threshold = module_config.ragThresholds[0]
        return getattr(threshold, CustomRagThreshold.IS_CUSTOM, False)

    def calculate_rag_flags(
        self, primitive: Primitive, primitives: list[Primitive] = None
    ):
        severities: dict[int, int] = {severity: 0 for severity in range(4)}
        threshold = self.get_threshold_data(primitive, self.config, primitives)
        severity_set = False
        if "severities" in threshold:
            for severity in threshold["severities"]:
                severities[severity] += 1
            severity_set = True
        else:
            for threshold_value in threshold.values():
                if RagThreshold.SEVERITY not in threshold_value:
                    continue
                severities[threshold_value[RagThreshold.SEVERITY]] += 1
                severity_set = True
        if not severity_set:
            severities[0] += 1
        flags = {
            "gray": severities[0] + severities[1],
            "amber": severities[2],
            "red": severities[3],
        }
        return {self.moduleId: threshold}, flags

    def validate_module_result(self, module_result: list[Primitive]):
        invalid_primitives = [
            str(p) for p in module_result if type(p) not in self.primitives
        ]
        if invalid_primitives:
            raise InvalidModuleResultException(
                f"Invalid primitives [{invalid_primitives}]"
            )

        if len(self.primitives) <= 1:
            return

        if len(module_result) < 2:
            raise InvalidModuleResultException(
                f"Not Enough primitives [{[str(p) for p in module_result]}] for {self.moduleId} module"
            )

        valid_primitives = self.primitives.copy()
        for primitive in module_result:
            try:
                valid_primitives.remove(type(primitive))
            except Exception:
                invalid_primitives.append(str(primitive))

        if invalid_primitives:
            raise InvalidModuleResultException(
                f"Too many primitives for module {self.moduleId}: [{[str(p) for p in module_result]}]"
            )

    @staticmethod
    def _apply_gray_flags_logic(primitives):
        """
        Applies gray flags logic, which is:
          - if even one rag, no gray flag should be reported
          - only one gray flag should be reported for a set of primitives.
        """
        rag_primitives = [
            i
            for i, p in enumerate(primitives)
            if p.flags and (p.flags[UnseenFlags.RED] or p.flags[UnseenFlags.AMBER])
        ]
        gray_primitives = [
            i
            for i, p in enumerate(primitives)
            if p.flags and p.flags["gray"] and i not in rag_primitives
        ]
        if not rag_primitives:
            if len(gray_primitives) >= 1:
                primitives[gray_primitives[0]].flags[UnseenFlags.GRAY] = 1
                for i in gray_primitives[1:]:
                    primitives[i].flags[UnseenFlags.GRAY] = 0
        else:
            for i in gray_primitives:
                primitives[i].flags[UnseenFlags.GRAY] = 0

    @staticmethod
    def _apply_most_severe_flags_logic(primitives):
        """
        this method makes sure that:
          - only 1 red flag is raised per submission if any calculated value
            falls within red thresholds
          - only 1 amber flag is raised per submission if any calculated value
            falls within amber thresholds and NO value fall within red
            threshold
          - only 1 grey flag is raised per submission if any calculated value
            falls within green thresholds and NO value fall within red or amber
            threshold
        """

        def most_severe_flag(primitive):
            if not primitive.flags:
                return UnseenFlags.GRAY
            flags = [UnseenFlags.RED, UnseenFlags.AMBER, UnseenFlags.GRAY]
            for color in flags:
                if color in primitive.flags and primitive.flags[color] > 0:
                    return color
            return UnseenFlags.GRAY

        indexed_primitive_severities = [
            (i, most_severe_flag(p)) for i, p in enumerate(primitives)
        ]
        indexed_primitive_severities = [
            (i, color)
            for i, color in indexed_primitive_severities
            if color != UnseenFlags.GRAY
        ]
        if not indexed_primitive_severities:
            return

        def empty_flags():
            return {
                UnseenFlags.RED: 0,
                UnseenFlags.AMBER: 0,
                UnseenFlags.GRAY: 0,
            }

        for primitive_index in [p[0] for p in indexed_primitive_severities]:
            primitives[primitive_index].flags = empty_flags()

        color_value = {UnseenFlags.RED: 3, UnseenFlags.AMBER: 2, UnseenFlags.GREEN: 1}
        result_flag = max(
            [ip[1] for ip in indexed_primitive_severities], key=lambda x: color_value[x]
        )
        first_index = indexed_primitive_severities[0][0]
        primitives[first_index].flags[result_flag] = 1

    @staticmethod
    def apply_overall_flags_logic(primitives):
        """
        Applies flags related rules on all of the primitives in parameters.
        It includes gray logic and most severe flag logic.

        Note: Modules with different logic should override this method.
        """
        Module._apply_most_severe_flags_logic(primitives)
        Module._apply_gray_flags_logic(primitives)

    @staticmethod
    def _get_primitives_old_values(
        primitives: list[Primitive], field_name: str
    ) -> list:
        values = []
        for old_primitive in primitives:
            value = getattr(old_primitive, field_name)
            if value:
                values.append(value)
        return values

    def _calculate_value(self, rag_type: RagThresholdType, value, avg_value):
        # calculate value to compare by the rag threshold type
        if rag_type == RagThresholdType.VALUE:
            # use primitive value if compared by VALUE
            return value
        elif rag_type == RagThresholdType.CHANGE_NUMBER:
            # use difference between primitive value and avg value if compared by CHANGE_NUMBER
            return value - avg_value
        elif rag_type == RagThresholdType.CHANGE_PERCENT:
            # use difference between primitive value and avg value in percent if compared by CHANGE_PERCENT
            return ((value - avg_value) * 100) / avg_value
        else:
            return None

    def _match_threshold(self, threshold_range: ThresholdRange, calc_value):
        condition = True
        # check if value is more then min value if minValue present
        if threshold_range.minValue:
            condition = threshold_range.minValue <= calc_value
        # check if value is less then maxValue if maxValue is present
        if threshold_range.maxValue:
            condition = condition and calc_value <= threshold_range.maxValue
        # check if value matches exact value if exact is present
        if threshold_range.exactValueStr:
            condition = condition and calc_value == threshold_range.exactValueStr
        return condition

    def trigger_key_actions(
        self,
        user: User,
        key_actions: list[KeyActionConfig],
        primitive: Primitive,
        config_body: dict,
        deployment_id: str,
        start_date: Union[str, datetime] = None,
        group_category: GroupCategory = None,
    ):
        pass

    @property
    def exportable(self):
        return True

    def validate_module_config(self, module_config: ModuleConfig):
        self.validate_config_body(module_config)

        if module_config.ragThresholds:
            self.validate_rag_thresholds(module_config.ragThresholds)

    def validate_rag_thresholds(self, rag_thresholds: list[RagThreshold]):
        for rag_threshold in rag_thresholds:
            found = False
            for primitive in self.primitives:
                if hasattr(primitive, rag_threshold.fieldName):
                    found = True
                    break
            if not found:
                msg = (
                    f"RAG error: {rag_threshold.fieldName} field "
                    f"is not supported by {self.moduleId} module"
                )
                raise InvalidRequestException(msg)

    def validate_config_body(self, module_config: ModuleConfig):
        schema = self.get_validation_schema()
        if schema:
            if not module_config.configBody:
                msg = f"ConfigBody is required for {module_config.moduleId}"
                raise InvalidModuleConfigBody(msg)
            try:
                validate(module_config.configBody, schema=schema)
            except Exception as error:
                raise ConvertibleClassValidationError(
                    "Field [{}.{}] with value [{}] has error [{}]".format(
                        ModuleConfig.__name__,
                        ModuleConfig.CONFIG_BODY,
                        module_config.configBody,
                        error.args,
                    )
                )
        else:
            if module_config.configBody:
                module_config.configBody = {}

    def _mc_filter_rule(self, mc: ModuleConfig, module_config_id: str = None):
        condition = mc.moduleId == self.moduleId
        if module_config_id:
            condition = condition and mc.id == module_config_id

        return condition and mc.status == EnableStatus.ENABLED

    def __str__(self):
        return f"Module({self.name}) > Primitives({[str(primitive) for primitive in self.primitives]})"

    def get_localization(self, user_language: str) -> dict:
        # not raising NotImplemented exception in order not to have linter notification
        # about not all abstract methods are implemented
        pass

    @staticmethod
    def change_primitives_based_on_config(
        primitives: list[Primitive], module_configs: list[ModuleConfig]
    ):
        pass


class AzModuleMixin:
    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        super().preprocess(primitives, user)
        for primitive in primitives:
            if type(primitive) == self.__class__.primitives[0]:
                must_not_be_present(skipped=primitive.skipped)
                d = primitive.to_dict()
                fields_we_can_submit = (
                    set(map(lambda x: x.name, fields(primitive)))
                    - set(map(lambda x: x.name, fields(Primitive)))
                    - primitive.FIELD_NAMES_TO_EXCLUDE
                )

                skipped_field_names = []
                for field_name in fields_we_can_submit:
                    if d[field_name] is None:
                        skipped_field_names.append(field_name)

                primitive.skipped = skipped_field_names
