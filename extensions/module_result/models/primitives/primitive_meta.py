""" Model for PrimitiveMeta """
from datetime import datetime

from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from sdk.common.utils.validators import default_datetime_meta


@convertibleclass
class PrimitiveMeta:
    # This class is intended to be constructed from data stored in the repository, so it
    # doesn't have all the FIELD_NAME constants of other domain objects.  They can be added
    # in future if required.
    UPDATE_DATE_TIME = "updateDateTime"
    CREATE_DATE_TIME = "createDateTime"
    NAME = "name"
    CREATE_ARGUMENT = "createArgument"
    CREATE_RESOLVER_NAME = "createResolverName"
    IS_DERIVED = "isDerived"

    # PrimitiveMetas should be unique by name so don't have an id field.
    name: str = required_field()
    createArgument: str = required_field()
    createResolverName: str = required_field()
    isDerived: bool = required_field(default=False)
    retrieveResolverName: str = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
