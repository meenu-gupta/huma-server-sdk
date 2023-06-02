from enum import Enum

from sdk.common.utils.convertible import (
    convertibleclass,
    required_field,
    url_field,
    default_field,
)

from extensions.common.s3object import S3Object
from extensions.deployment.models.consent.consent_section import (
    ConsentSection,
    ConsentSectionOptions,
)


@convertibleclass
class EConsentSectionOptions(ConsentSectionOptions):
    """EConsent section model class"""


@convertibleclass
class EConsentSection(ConsentSection):
    """EConsent section model class"""

    CONTENT_TYPE = "contentType"
    THUMBNAIL_URL = "thumbnailUrl"
    THUMBNAIL_LOCATION = "thumbnailLocation"
    VIDEO_LOCATION = "videoLocation"
    VIDEO_URL = "videoUrl"

    class EConsentSectionType(Enum):
        INTRODUCTION = "INTRODUCTION"
        PURPOSE = "PURPOSE"
        REVIEW_TO_SIGN = "REVIEW_TO_SIGN"
        DURING_THE_TRIAL = "DURING_THE_TRIAL"
        CONSENT_FORM = "CONSENT_FORM"

    class ContentType(Enum):
        IMAGE = "IMAGE"
        VIDEO = "VIDEO"

    type: EConsentSectionType = required_field()
    contentType: ContentType = required_field()
    thumbnailUrl: str = url_field()
    thumbnailLocation: S3Object = default_field()
    videoUrl: str = url_field()
    videoLocation: S3Object = default_field()
