from enum import Enum


class OnfidoReportNameType(Enum):
    IDENTITY_ENHANCED = "identity_enhanced"
    DOCUMENT = "document"
    WATCHLIST_STANDARD = "watchlist_standard"
    FACIAL_SIMILARITY_PHOTO = "facial_similarity_photo"
    FACIAL_SIMILARITY_PHOTO_FULLY_AUTO = "facial_similarity_photo_fully_auto"
    FACIAL_SIMILARITY_VIDEO = "facial_similarity_video"
    KNOWN_FACES = "known_faces"
    RIGHT_TO_WORK = "right_to_work"
    DOCUMENT_WITH_ADDRESS_INFORMATION = "document_with_address_information"
    DOCUMENT_WITH_DRIVING_LICENCE_INFORMATION = (
        "document_with_driving_licence_information"
    )
    WATCHLIST_ENHANCED = "watchlist_enhanced"
    WATCHLIST_PEPS_ONLY = "watchlist_peps_only"
    WATCHLIST_SANCTIONS_ONLY = "watchlist_sanctions_only"
    PROOF_OF_ADDRESS = "proof_of_address"

    @staticmethod
    def has_value(value):
        return value in {v.value for v in OnfidoReportNameType}


class IdentityVerificationAction(Enum):
    GenerateIdentityVerificationToken = "GenerateIdentityVerificationToken"
    CreateUserVerificationLog = "CreateUserVerificationLog"
