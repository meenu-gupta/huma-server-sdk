from dataclasses import field
from enum import IntEnum

from extensions.module_result.models.primitives import Primitive
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.convertible import (
    required_field,
    convertibleclass,
    meta,
    default_field,
)
from sdk.common.utils.validators import validate_range


class HipAffected(IntEnum):
    RIGHT = 0
    LEFT = 1
    BOTH = 2


@convertibleclass
class HipData:
    HIP_AFFECTED = "hipAffected"
    SCORE = "score"

    pain: int = required_field(metadata=meta(validate_range(1, 5)))
    washing: int = required_field(metadata=meta(validate_range(1, 5)))
    transport: int = required_field(metadata=meta(validate_range(1, 5)))
    socks: int = required_field(metadata=meta(validate_range(1, 5)))
    shopping: int = required_field(metadata=meta(validate_range(1, 5)))
    walking: int = required_field(metadata=meta(validate_range(1, 5)))
    stairs: int = required_field(metadata=meta(validate_range(1, 5)))
    standing: int = required_field(metadata=meta(validate_range(1, 5)))
    limping: int = required_field(metadata=meta(validate_range(1, 5)))
    shooting: int = required_field(metadata=meta(validate_range(1, 5)))
    interference: int = required_field(metadata=meta(validate_range(1, 5)))
    bed: int = required_field(metadata=meta(validate_range(1, 5)))
    score: int = field(default=0)
    hipAffected: HipAffected = default_field()

    def set_score(self, hip_affected: HipAffected, score: int):
        self.set_field_value(self.SCORE, score)
        self.set_field_value(self.HIP_AFFECTED, hip_affected)


@convertibleclass
class OxfordHipScore(Primitive):
    HIP_AFFECTED = "hipAffected"
    HIPS_DATA = "hipsData"
    RIGHT_HIP_SCORE = "rightHipScore"
    LEFT_HIP_SCORE = "leftHipScore"

    hipAffected: HipAffected = required_field()
    hipsData: list[HipData] = required_field()
    rightHipScore: int = default_field()
    leftHipScore: int = default_field()

    @classmethod
    def validate(cls, request):
        cls._validate_if_hips_data_present(request.hipsData)
        if request.hipAffected == HipAffected.BOTH.value:
            cls._validate_if_both_hips_present(request.hipsData)

    @staticmethod
    def _validate_if_both_hips_present(hips_data: list[HipData]):
        if len(hips_data) != 2:
            raise InvalidRequestException("Missing data for both hips")

    @staticmethod
    def _validate_if_hips_data_present(hips_data: list[HipData]):
        if len(hips_data) < 1:
            raise InvalidRequestException("Missing data for hips")

    def get_hip_score(self, field_name: str, default_value: int = 0) -> int:
        val = getattr(self, field_name, None)
        return val if val is not None else default_value
