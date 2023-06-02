import abc
from abc import ABC
from dataclasses import field
from datetime import date

from sdk import convertibleclass, meta
from sdk.common.common_models.user_models import AddressObject
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    validate_entity_name,
    utc_date_to_str,
    utc_str_to_date,
    default_email_meta,
)


@convertibleclass
class IdentityVerificationApplicant:
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    DOB = "dob"
    ID_NUMBERS = "id_numbers"
    ADDRESS = "address"

    first_name: str = required_field(metadata=meta(validate_entity_name))
    last_name: str = required_field(metadata=meta(validate_entity_name))
    email: str = default_field(metadata=default_email_meta())
    dob: date = default_field(
        metadata=meta(field_to_value=utc_date_to_str, value_to_field=utc_str_to_date),
    )
    id_numbers: list[str] = default_field()
    address: AddressObject = default_field()


@convertibleclass
class IdentityVerificationCheck:
    APPLICANT_ID = "applicant_id"
    REPORT_NAMES = "report_names"
    DOCUMENT_IDS = "document_ids"
    APPLICANT_PROVIDES_DATA = "applicant_provides_data"
    ASYNCHRONOUS = "asynchronous"
    TAGS = "tags"
    SUPPRESS_FORM_EMAILS = "suppress_form_emails"
    REDIRECT_URI = "redirect_uri"
    CONSIDER = "consider"

    applicant_id: str = required_field()
    report_names: list[str] = required_field()
    document_ids: list[str] = default_field()
    applicant_provides_data: bool = field(default=False)
    asynchronous: bool = field(default=True)
    tags: list[str] = default_field()
    suppress_form_emails: bool = default_field()
    redirect_uri: str = default_field()
    consider: list[str] = default_field()


class IdentityVerificationAdapter(ABC):
    @abc.abstractmethod
    def create_applicant(self, applicant: IdentityVerificationApplicant) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def generate_sdk_token(self, applicant_id: str, application_id: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def create_check(self, check: IdentityVerificationCheck):
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve_verification_check(self, check_id: str) -> dict:
        raise NotImplementedError
