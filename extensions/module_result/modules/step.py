from datetime import datetime, timedelta, time
from typing import Optional

from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Step

from extensions.module_result.models.primitives import Primitive
from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.repository.module_result_repository import (
    ModuleResultRepository,
)
from sdk.common.utils.inject import autoparams
from .visualizer import StepHTMLVisualizer


class StepModule(Module):
    moduleId = "Step"
    primitives = [Step]
    visualizer = StepHTMLVisualizer

    @autoparams("repo")
    def preprocess(
        self, primitives: list[Primitive], user: User, repo: ModuleResultRepository
    ):
        steps_in_week = dict()
        last_primitive_in_week = dict()
        primitives.sort(key=lambda p: p.startDateTime)
        for pid, primitive in enumerate(primitives):
            if not isinstance(primitive, Step):
                continue
            primitive_date_time = primitive.startDateTime
            week_start_date_time = primitive_date_time - timedelta(
                days=primitive_date_time.weekday()
            )
            next_week_start_date = week_start_date_time + timedelta(days=7)
            week_start_date = datetime.combine(week_start_date_time, time.min)
            week_end_date = datetime.combine(next_week_start_date, time.min)
            week_number = primitive_date_time.isocalendar()[1]
            if week_number in steps_in_week:
                steps_in_week[week_number] += primitive.value
            else:
                same_week_primitives = repo.retrieve_primitives(
                    user_id=user.id,
                    module_id=self.moduleId,
                    primitive_name=Step.__name__,
                    skip=None,
                    limit=None,
                    direction=None,
                    from_date_time=week_start_date,
                    to_date_time=week_end_date,
                )
                steps_in_week[week_number] = primitive.value + sum(
                    map(lambda p: p.value, same_week_primitives)
                )
                repo.reset_flags(
                    user_id=primitive.userId,
                    module_id=primitive.moduleId,
                    start_date_time=week_start_date,
                    end_date_time=week_end_date,
                )
            primitive.weeklyTotal = steps_in_week[week_number]
            last_primitive_in_week[week_number] = pid

        is_last_primitive_in_week = [False] * len(primitives)
        for pid in last_primitive_in_week.values():
            is_last_primitive_in_week[pid] = True
        for pid in range(len(primitives)):
            if not is_last_primitive_in_week[pid]:
                primitives[pid].weeklyTotal = None

    def calculate_threshold(
        self,
        target_primitive: Primitive,
        module_config: ModuleConfig,
        primitives: list[Primitive],
    ) -> Optional[dict]:
        if not module_config.ragThresholds:
            return

        threshold = {}
        for rag in module_config.ragThresholds:
            if not rag.enabled:
                continue

            threshold_by_field_name = threshold.get(Step.WEEKLY_TOTAL)
            if not threshold_by_field_name:
                threshold[Step.WEEKLY_TOTAL] = None

            if (
                threshold_by_field_name
                and rag.severity < threshold_by_field_name.severity
            ):
                continue

            for threshold_range in rag.thresholdRange:
                if target_primitive.weeklyTotal is not None and self._match_threshold(
                    threshold_range, target_primitive.weeklyTotal
                ):
                    threshold[Step.WEEKLY_TOTAL] = rag
                    break
        return threshold

    def calculate_rag_flags(
        self, primitive: Primitive, primitives: list[Primitive] = None
    ):
        if not isinstance(primitive, Step) or primitive.weeklyTotal is not None:
            return super().calculate_rag_flags(primitive)
        threshold = self.get_threshold_data(primitive, self.config, [])
        flags = {
            "gray": 0,
            "amber": 0,
            "red": 0,
        }
        return {self.moduleId: threshold}, flags
