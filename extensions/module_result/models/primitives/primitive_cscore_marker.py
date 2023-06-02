""" Model for C-Score Marker object """

from sdk.common.utils.convertible import convertibleclass
from .primitive import Primitive


@convertibleclass
class CScoreMarker(Primitive):
    """CScoreMarker model.  This Primitive simply marks that the primitives required to
    calculate a C-Score have been submitted."""

    pass
