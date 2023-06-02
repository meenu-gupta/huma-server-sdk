"""model for symptom object"""
from sdk.common.utils.convertible import convertibleclass, required_field, default_field
from .primitive import Primitive


@convertibleclass
class ComplexSymptomValue:
    """ComplexSymptom model"""

    NAME = "name"
    SEVERITY = "severity"

    name: str = required_field()
    severity: int = default_field()


@convertibleclass
class Symptom(Primitive):
    """Symptom model"""

    COMPLEX_VALUES = "complexValues"

    # value field is for backward compatibility only
    value: list[str] = default_field()
    complexValues: list[ComplexSymptomValue] = default_field()
