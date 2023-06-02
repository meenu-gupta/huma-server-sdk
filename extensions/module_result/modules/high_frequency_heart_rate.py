from extensions.authorization.models.user import UnseenFlags
from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import (
    HighFrequencyHeartRate,
    Primitive,
)


class HighFrequencyHeartRateModule(Module):
    moduleId = "HighFrequencyHeartRate"
    primitives = [HighFrequencyHeartRate]
    ragEnabled = True

    def apply_overall_flags_logic(self, primitives: list[Primitive]):
        if not self.config.ragThresholds and primitives:
            frequency_count = 0
            for p in primitives:
                if p.dataType == HighFrequencyHeartRate.DataType.MULTIPLE_VALUE:
                    for value in p.multipleValues or []:
                        if value.p:
                            for v in value.p.values():
                                frequency_count += 1 if v else 0
                elif p.dataType in (
                    HighFrequencyHeartRate.DataType.PPG_VALUE,
                    HighFrequencyHeartRate.DataType.SINGLE_VALUE,
                ):
                    frequency_count += 1 if p.value else 0
            primitives[0].flags = {
                UnseenFlags.RED: 0,
                UnseenFlags.AMBER: 0,
                UnseenFlags.GRAY: frequency_count,
            }
