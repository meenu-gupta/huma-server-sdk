""" Model for WoundPhoto object """
from sdk.common.utils.convertible import convertibleclass
from .primitive_photo import Photo


@convertibleclass  # pragma: no cover
class WoundPhoto(Photo):
    """WoundPhoto model - this is just a marker class"""
