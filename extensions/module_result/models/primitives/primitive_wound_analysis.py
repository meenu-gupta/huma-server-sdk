""" Model for Wound Analysis Result objects """
from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class WoundAnalysis(Primitive):
    """WoundAnalysis model"""

    # IMPORTANT NOTES!!!!
    # 1. startDateTime must be set to that of the wound photo that triggered the analysis,
    # so it's possible to find and correlate the photo and the analysis in Dynamo and ElasticSearch
    # 2. fullAnalysis can be about 50kB of JSON - TODO test this with larger photos

    class Error(Enum):
        NO_DOT = 1  # Can't find the green dot in the photo
        NO_WOUND = 2  # Can't find a wound in the photo
        EXCEEDS_MAX_ANGLE = 3  # Camera angle too steep
        API_ERROR = 4  # Problem communicating with analysis API

    errors: list[Error] = default_field()
    woundId: int = default_field()
    woundEvaluationId: int = default_field()
    woundAnalysisId: int = default_field()
    # value is the total area in cm^2 extracted from the full analysis result...
    value: float = required_field(metadata=meta(value_to_field=float))
    # ... which is stored in fullAnalysis.  This is the exact JSON that came back from the API.
    # TODO do we want to prevent Users/patients from retrieving fullAnalysis?
    fullAnalysis: dict = default_field()
    # FIXME override __str__ to trim down coordinates?
