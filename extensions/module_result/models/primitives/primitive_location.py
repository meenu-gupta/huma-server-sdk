""" Location model - for location entered manually or occasionally as opposed to e.g. live GPS. """
from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    default_field,
)
from .primitive import Primitive


@convertibleclass
class Location(Primitive):
    """Location model - for location entered manually or occasionally as opposed to e.g. live GPS."""

    LOCATION_QUESTION = "locationQuestion"
    LOCATION_PROVIDER = "locationProvider"

    # TODO move these enums out so they can be shared with a future LocationFast?
    class LocationProviderType(Enum):
        DATAHUB = "DATAHUB"
        # add GOOGLE_PLACES etc as needed

    class LocationQuestionType(Enum):
        WHERE_LIVING = "WHERE_LIVING"
        # add WHERE_STUDYING, WHERE_WORKING, WHERE_TRAVELLED etc as needed

    countryName: str = default_field()
    geonameId: int = default_field()
    # latitude and longitude will not be populated on creation, initially, but they might be added on retrieval
    latitude: float = default_field(
        metadata=meta(lambda x: x is None or -180 < x < 180, value_to_field=float),
    )
    longitude: float = default_field(
        metadata=meta(lambda x: x is None or -90 < x < 90, value_to_field=float),
    )
    # Could add bbox (bounding box) if needed, but there are at least two flavours of them so wait until there's a need
    locationQuestion: LocationQuestionType = required_field()
    locationProvider: LocationProviderType = required_field()
    placeName: str = default_field()
