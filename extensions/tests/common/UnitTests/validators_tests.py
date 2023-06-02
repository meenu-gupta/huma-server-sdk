from extensions.common.validators import validate_fields_for_cls
from sdk import convertibleclass
from sdk.common.utils.convertible import ConvertibleClassValidationError, default_field


@convertibleclass
class Test1:
    field4: int = default_field()
    field5: str = default_field()


@convertibleclass
class Test2:
    field1: int = default_field()
    field2: str = default_field()
    field3: Test1 = default_field()


def test_success_validate_fields():
    fields = {"field1"}
    try:
        valid = validate_fields_for_cls(fields, Test2)
        assert valid is True
    except ConvertibleClassValidationError as e:
        assert True is False, e


def test_success_validate_fields_multiple():
    fields = {"field1", "field2"}
    try:
        valid = validate_fields_for_cls(fields, Test2)
        assert valid is True
    except ConvertibleClassValidationError as e:
        assert True is False, e


def test_failure_validate_fields():
    fields = {"field0"}
    try:
        validate_fields_for_cls(fields, Test2)
    except Exception as e:
        assert isinstance(e, ConvertibleClassValidationError)
        assert "field0" in str(e)


def test_failure_validate_fields_multiple():
    fields = {"field0", "field-1"}
    try:
        validate_fields_for_cls(fields, Test2)
    except Exception as e:
        assert isinstance(e, ConvertibleClassValidationError)
        assert "field0" in str(e)
        assert "field-1" in str(e)


def test_failure_validate_fields_one_field_correct():
    fields = {"field0", "field1"}
    try:
        validate_fields_for_cls(fields, Test2)
    except Exception as e:
        assert isinstance(e, ConvertibleClassValidationError)
        assert "field0" in str(e)
        assert "field1" not in str(e)


def test_success_validate_fields_nested():
    fields = {"field3.field4"}
    try:
        valid = validate_fields_for_cls(fields, Test2)
        assert valid is True
    except ConvertibleClassValidationError as e:
        assert True is False, e


def test_failure_validate_fields_nested():
    fields = {"field3.field0"}
    try:
        valid = validate_fields_for_cls(fields, Test2)
        assert valid is True
    except Exception as e:
        assert isinstance(e, ConvertibleClassValidationError)
        assert "field0" in str(e)


def test_failure_validate_fields_nested_in_non_nested():
    fields = {"field1.field1"}
    try:
        valid = validate_fields_for_cls(fields, Test2)
        assert valid is True
    except Exception as e:
        assert isinstance(e, ConvertibleClassValidationError)
