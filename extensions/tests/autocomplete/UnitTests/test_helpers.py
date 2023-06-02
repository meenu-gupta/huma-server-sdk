from extensions.autocomplete.models.autocomplete_metadata import AutocompleteMetadata
from extensions.common.s3object import S3Object
from sdk.common.localization.utils import Language


def get_sample_autocomplete_search_result_request_dict() -> dict:
    return {"listEndpointId": "Medications", "search": "status"}


def sample_autocomplete_metadata() -> dict:
    return {
        AutocompleteMetadata.MODULE_ID: "module_id",
        AutocompleteMetadata.LANGUAGE: Language.EN,
        AutocompleteMetadata.S3_OBJECT: {
            S3Object.BUCKET: "bucket_name",
            S3Object.KEY: "bucket_key",
            S3Object.REGION: "eu",
        },
    }
