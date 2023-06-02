from sdk.common.exceptions.exceptions import DetailedException, ErrorCodes


class InvalidSortFieldsException(DetailedException):
    def __init__(self, fields_list):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"Fields {fields_list} are not valid for sorting",
            status_code=400,
        )


class InvalidFieldsException(DetailedException):
    def __init__(self, fields_list):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"Fields {fields_list} are not valid for this request",
            status_code=400,
        )


class InvalidModuleException(DetailedException):
    def __init__(self, module_name):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"module [{module_name}] is not valid",
            status_code=400,
        )


class UserAttributeMissingError(DetailedException):
    def __init__(self, field_name):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"User attribute [{field_name}] is missing",
            status_code=400,
        )


class InvalidCarePlanGroupException(DetailedException):
    def __init__(self, care_plan_group_id):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"CarePlanGroup [{care_plan_group_id}] is not valid",
            status_code=400,
        )


class CarePlanGroupFieldMissingError(DetailedException):
    def __init__(self, field_name):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"CarePlanGroup field [{field_name}] is missing",
            status_code=400,
        )


class InvalidPatchChangeType(DetailedException):
    def __init__(self, change_type):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"CarePlanGroup ChangeType [{change_type}] is invalid",
            status_code=400,
        )


class InvalidGenderOptionValueException(DetailedException):
    def __init__(self, value):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"GenderOption Value [{value}] is not valid",
            status_code=400,
        )


class InvalidEthnicityOptionValueException(DetailedException):
    def __init__(self, value):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"EthnicityOption Value [{value}] is not valid",
            status_code=400,
        )


class InvalidModuleForPreferredUnitException(DetailedException):
    def __init__(self, module):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"Module [{module}] does not accept PreferredUnit.",
            status_code=400,
        )


class InvalidMeasureUnitException(DetailedException):
    def __init__(self, unit):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"MeasureUnit [{unit}] is invalid.",
            status_code=400,
        )


class InvalidIdentityReportNameException(DetailedException):
    def __init__(self, report_name):
        super().__init__(
            code=ErrorCodes.INVALID_REQUEST,
            debug_message=f"Identity Report Name [{report_name}] is invalid.",
            status_code=400,
        )
