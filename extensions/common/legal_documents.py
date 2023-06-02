from extensions.common.s3object import S3Object
from sdk import convertibleclass
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils.convertible import url_field, default_field
from sdk.common.utils.inject import autoparams


@convertibleclass
class LegalDocument:
    TERM_AND_CONDITION_URL = "termAndConditionUrl"
    PRIVACY_POLICY_URL = "privacyPolicyUrl"
    EULA_URL = "eulaUrl"
    TERM_AND_CONDITION_OBJECT = "termAndConditionObject"
    PRIVACY_POLICY_OBJECT = "privacyPolicyObject"
    EULA_OBJECT = "eulaObject"

    termAndConditionUrl: str = url_field()
    privacyPolicyUrl: str = url_field()
    eulaUrl: str = url_field()
    privacyPolicyObject: S3Object = default_field()
    termAndConditionObject: S3Object = default_field()
    eulaObject: S3Object = default_field()

    @autoparams()
    def set_presigned_urls_for_legal_docs(self, file_storage: FileStorageAdapter):
        legal_docs_fields_mapping = {
            self.PRIVACY_POLICY_URL: self.privacyPolicyObject,
            self.TERM_AND_CONDITION_URL: self.termAndConditionObject,
            self.EULA_URL: self.eulaObject,
        }
        for doc_url_field, file_obj in legal_docs_fields_mapping.items():
            url = getattr(self, doc_url_field)
            if not url and file_obj and file_obj.bucket and file_obj.key:
                url = file_storage.get_pre_signed_url(file_obj.bucket, file_obj.key)
                self.set_field_value(field=doc_url_field, field_value=url)
