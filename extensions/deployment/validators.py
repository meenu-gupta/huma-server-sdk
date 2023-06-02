from collections import Callable
from datetime import date, datetime

import isodate

from extensions.autocomplete.models.modules.az_vaccine_batch_number_autocomplete import (
    AZVaccineBatchNumberModule,
)
from extensions.deployment.models.deployment import SurgeryDateRule, FieldValidator
from extensions.exceptions import InvalidSurgeryDateError
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import utc_date_to_str


def validate_surgery_date(surgery_date: date, surgery_date_rule: SurgeryDateRule):
    dt_now = datetime.now().date()

    past_range_duration = SurgeryDateRule.DEFAULT_PAST_RANGE
    if surgery_date_rule and surgery_date_rule.maxPastRange:
        past_range_duration = surgery_date_rule.maxPastRange

    past_timedelta = isodate.parse_duration(past_range_duration)
    past_limit_date = dt_now - past_timedelta
    if past_limit_date > surgery_date:
        raise InvalidSurgeryDateError(
            message=f"Surgery date should be after {past_limit_date}"
        )

    future_range_duration = SurgeryDateRule.DEFAULT_FUTURE_RANGE
    if surgery_date_rule and surgery_date_rule.maxFutureRange:
        future_range_duration = surgery_date_rule.maxFutureRange

    future_timedelta = isodate.parse_duration(future_range_duration)
    future_limit_date = dt_now + future_timedelta
    if future_limit_date < surgery_date:
        raise InvalidSurgeryDateError(
            message=f"Surgery date should be before {future_limit_date}"
        )


def validate_vaccination_batch_number(vaccine_batch_number: str) -> bool:
    az_vaccine_module = AZVaccineBatchNumberModule()
    search_results = az_vaccine_module.retrieve_search_result(
        vaccine_batch_number, exact_word=True
    )
    return len(search_results) == 1


def build_date_time_validator(validator: FieldValidator) -> Callable:
    today = datetime.utcnow()

    def validate(field: str, value: datetime):
        if validator.minISODuration:
            min_duration = isodate.parse_duration(validator.minISODuration)
            start = (today + min_duration).date()

            if value < start:
                raise ConvertibleClassValidationError(
                    f"{field} field should be more than {utc_date_to_str(start)}"
                )

        if validator.maxISODuration:
            max_duration = isodate.parse_duration(validator.maxISODuration)
            end = (today + max_duration).date()

            if value > end:
                raise ConvertibleClassValidationError(
                    f"{field} field should be less than {utc_date_to_str(end)}"
                )

        if validator.max:
            if value > validator.max:
                raise ConvertibleClassValidationError(
                    f"{field} field should be less than {utc_date_to_str(validator.max)}"
                )

        if validator.min:
            if value < validator.min:
                raise ConvertibleClassValidationError(
                    f"{field} field should be more than {utc_date_to_str(validator.min)}"
                )

    return validate
