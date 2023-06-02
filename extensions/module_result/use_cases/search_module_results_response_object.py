from extensions.common.s3object import FlatBufferS3Object
from extensions.module_result.common.flatbuffer_utils import ecg_data_points_to_array
from extensions.module_result.models.primitives import (
    Primitive,
    ECGHealthKit,
    ECGReading,
)
from sdk import convertibleclass, meta
from sdk.common.usecase import response_object
from sdk.common.utils.convertible import required_field


class SearchModuleResultsResponseObject(response_object.Response):
    def __init__(self, results: dict):
        super().__init__(value=results)


class RetrieveModuleResultResponseObject(response_object.Response):
    def __init__(self, result: Primitive):
        super().__init__(value=result)


@convertibleclass
class ResponseECGReading(ECGReading):
    dataPoints: FlatBufferS3Object = required_field(
        metadata=meta(field_to_value=ecg_data_points_to_array)
    )


@convertibleclass
class HealthKitResponseData(ECGHealthKit):
    ecgReading: ResponseECGReading = required_field()
