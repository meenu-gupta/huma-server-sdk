import unittest
from dataclasses import field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any

from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    is_list_field,
    ConvertibleClassValidationError,
    default_field,
)
from sdk.common.utils.validators import utc_date_to_str, validate_len


@convertibleclass
class ExampleNestedClass:
    class TestEnum(Enum):
        T1 = "TEST1"
        T2 = "TEST2"

    nf1: str = None
    nf2: TestEnum = TestEnum.T1
    nf3: datetime = default_field(metadata=meta(field_to_value=utc_date_to_str))


@convertibleclass
class ExampleClass:
    f1: int = None
    f2: str = None
    f3: bool = None
    f4: float = None
    f5: ExampleNestedClass = None


class ConvertibleClassToDictTestCase(unittest.TestCase):
    def test_simple_class(self):
        @convertibleclass
        class TestClass:
            f1: int = field(default=1)
            f2: list[int] = field(default_factory=int)
            f3: bool = False
            f4: float = 0.0
            f5: datetime = default_field(metadata=meta(field_to_value=utc_date_to_str))
            f6: list[str] = field(default_factory=str)

        dt = datetime.utcnow()
        test_class = TestClass(f1=12, f2="str", f3=True, f4=12.12, f5=dt, f6=["test"])
        d = test_class.to_dict()
        self.assertDictEqual(
            d,
            {
                "f1": 12,
                "f2": "str",
                "f3": True,
                "f4": 12.12,
                "f5": dt.strftime("%Y-%m-%d"),
                "f6": ["test"],
            },
        )

    def test_simple_class_with_enum(self):
        @convertibleclass
        class TestClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            f1: int = 0
            f2: str = None
            f3: bool = False
            f4: float = 0.0
            f5: TestEnum = TestEnum.T1

        test_class = TestClass(
            f1=12, f2="str", f3=True, f4=12.12, f5=TestClass.TestEnum.T1
        )
        d = test_class.to_dict()
        self.assertDictEqual(
            d, {"f1": 12, "f2": "str", "f3": True, "f4": 12.12, "f5": "T1"}
        )

    def test_simple_class_with_int_enum(self):
        @convertibleclass
        class TestClass:
            class TestEnum(IntEnum):
                T1 = 1
                T2 = 2

            f1: TestEnum = TestEnum.T1

        test_class = TestClass(f1=TestClass.TestEnum.T1)
        d = test_class.to_dict()
        self.assertDictEqual(d, {"f1": 1})

    def test_simple_class_with_array(self):
        @convertibleclass
        class TestClass:
            f1: int = 0
            f2: str = None
            f3: bool = False
            f4: float = 0.0
            f5: list[str] = None

        test_object = TestClass(f1=12, f2="str", f3=True, f4=12.12, f5=["a1", "a2"])
        d = test_object.to_dict()
        self.assertDictEqual(
            d, {"f1": 12, "f2": "str", "f3": True, "f4": 12.12, "f5": ["a1", "a2"]}
        )

    def test_simple_class_with_nested_class(self):
        dt = datetime.utcnow()
        test_class = ExampleClass(
            f1=12,
            f2="str",
            f3=True,
            f4=12.12,
            f5=ExampleNestedClass(
                nf1="strnf1", nf2=ExampleNestedClass.TestEnum.T1, nf3=dt
            ),
        )
        d = test_class.to_dict(include_none=False)
        self.assertDictEqual(
            d,
            {
                "f1": 12,
                "f2": "str",
                "f3": True,
                "f4": 12.12,
                "f5": {"nf1": "strnf1", "nf2": "T1", "nf3": dt.strftime("%Y-%m-%d")},
            },
        )

    def test_equality_of_simple_class_with_nested_class(self):
        test_class1 = ExampleClass(
            f1=12,
            f2="str",
            f3=True,
            f4=12.12,
            f5=ExampleNestedClass(nf1="strnf1", nf2=ExampleNestedClass.TestEnum.T1),
        )
        test_class2 = ExampleClass(
            f1=12,
            f2="str",
            f3=True,
            f4=12.12,
            f5=ExampleNestedClass(nf1="strnf1", nf2=ExampleNestedClass.TestEnum.T1),
        )
        self.assertEqual(test_class1, test_class2)

    def test_non_equality_of_simple_class_with_nested_class(self):
        @convertibleclass
        class TestNestedClass:
            class TestEnum(Enum):
                T1 = "TEST1"
                T2 = "TEST2"

            nf1: str = None
            nf2: TestEnum = TestEnum.T1

        @convertibleclass
        class TestClass:
            f1: int = None
            f2: str = None
            f3: bool = None
            f4: float = None
            f5: TestNestedClass = None

        test_class1 = TestClass(
            f1=12,
            f2="str",
            f3=True,
            f4=12.12,
            f5=TestNestedClass(nf1="strnf1", nf2=TestNestedClass.TestEnum.T1),
        )
        test_class2 = TestClass(
            f1=12,
            f2="str",
            f3=True,
            f4=12.12,
            f5=TestNestedClass(nf1="strnf2", nf2=TestNestedClass.TestEnum.T1),
        )
        self.assertNotEqual(test_class1, test_class2)

    def test_complex_class(self):
        def custom_list_conversion(data: list):
            return [instance.to_dict(ignored_fields=["nf3"]) for instance in data]

        @convertibleclass
        class TestNestedClass:
            class TestEnum(Enum):
                T1 = "TEST1"
                T2 = "TEST2"

            nf1: str = None
            nf2: TestEnum = TestEnum.T1
            nf3: float = default_field(metadata=meta(field_to_value=int))
            nlf1: list[TestEnum] = field(default_factory=list)

        @convertibleclass
        class TestClass:
            f1: int = None
            f2: str = None
            f3: bool = None
            f4: float = None
            f5: list[TestNestedClass] = None
            f6: list = default_field(
                metadata=meta(field_to_value=custom_list_conversion)
            )

        test_class = TestClass(
            f1=12,
            f2="str",
            f3=True,
            f4=12.12,
            f5=[
                TestNestedClass(nf1="strnf1", nf2=TestNestedClass.TestEnum.T1),
                TestNestedClass(
                    nf1="strnf2",
                    nf2=TestNestedClass.TestEnum.T2,
                    nlf1=[TestNestedClass.TestEnum.T1, TestNestedClass.TestEnum.T2],
                ),
            ],
            f6=[TestNestedClass(nf1="strnf1", nf3=28.12)],
        )
        d = test_class.to_dict()
        self.assertDictEqual(
            d,
            {
                "f1": 12,
                "f2": "str",
                "f3": True,
                "f4": 12.12,
                "f5": [
                    {"nf1": "strnf1", "nf2": "T1", "nf3": None, "nlf1": []},
                    {"nf1": "strnf2", "nf2": "T2", "nf3": None, "nlf1": ["T1", "T2"]},
                ],
                "f6": [{"nf1": "strnf1", "nf2": "T1", "nf3": 28.12, "nlf1": []}],
            },
        )

    def test_convert_list_field_with_nested_object_with_field_to_value(self):
        def custom_list_conversion(data: list):
            return [instance.to_dict(ignored_fields=["nf2"]) for instance in data]

        @convertibleclass
        class TestNestedClass:
            nf1: str = None
            nf2: float = default_field(metadata=meta(field_to_value=int))

        @convertibleclass
        class TestClass:
            f1: int = None
            f2: list = default_field(
                metadata=meta(field_to_value=custom_list_conversion)
            )
            f3: list = default_field()

        test_class = TestClass(
            f1=12,
            f2=[
                TestNestedClass(nf1="strnf1", nf2=25.78),
                TestNestedClass(nf1="strnf2", nf2=13.12),
            ],
            f3=[
                TestNestedClass(nf1="strnf1", nf2=25.78),
                TestNestedClass(nf1="strnf2", nf2=13.12),
            ],
        )
        result_dict = test_class.to_dict()
        self.assertDictEqual(
            result_dict,
            {
                "f1": 12,
                "f2": [
                    {"nf1": "strnf1", "nf2": 25.78},
                    {"nf1": "strnf2", "nf2": 13.12},
                ],
                "f3": [
                    {"nf1": "strnf1", "nf2": 25},
                    {"nf1": "strnf2", "nf2": 13},
                ],
            },
        )

    def test_simple_inheritance(self):
        @convertibleclass
        class TestParentClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            nf1: str = default_field(metadata=meta(validate_len(min=1)))
            nf2: TestEnum = TestEnum.T1

        @convertibleclass
        class TestChildClass(TestParentClass):
            f2: str = default_field(metadata=meta(validate_len(min=1)))
            f3: bool = None
            f4: float = None

        test_class = TestChildClass(
            f2="str", f3=True, f4=12.12, nf1="strnf1", nf2=TestParentClass.TestEnum.T1
        )
        d = test_class.to_dict()
        self.assertDictEqual(
            d, {"f2": "str", "f3": True, "f4": 12.12, "nf1": "strnf1", "nf2": "T1"}
        )


class ConvertibleClassFromDictTestCase(unittest.TestCase):
    def test_validator_for_enum_field(self):
        @convertibleclass
        class TestClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            f1: TestEnum = default_field()
            f2: Any = default_field(metadata=meta(required=True))
            f3: datetime = default_field(
                metadata=meta(
                    value_to_field=lambda n: datetime.strptime(n, "%Y-%m-%d")
                ),
            )

        d = {"f1": "T1", "f2": "test", "f3": "1980-01-01"}
        converted_dict: TestClass = TestClass.from_dict(d)
        self.assertEqual(converted_dict.f1, TestClass.TestEnum.T1)

    def test_validator_for_int_enum_field(self):
        @convertibleclass
        class TestClass:
            class TestEnum(IntEnum):
                T1 = 1
                T2 = 2

            f1: TestEnum = default_field()

        d = {"f1": 1}
        converted_dict: TestClass = TestClass.from_dict(d)
        self.assertEqual(converted_dict.f1, TestClass.TestEnum.T1)

    def test_validator_for_field(self):
        @convertibleclass
        class TestClass:
            f1: int = 0
            f2: str = default_field(metadata=meta(validate_len(1, 1)))

        d = {"f1": 12, "f2": "str"}
        with self.assertRaises(Exception):
            TestClass.from_dict(d)

    def test_simple_type_validators(self):
        @convertibleclass
        class TestClass:
            f1: int = default_field(metadata=meta(int))
            f2: bool = default_field(metadata=meta(bool))
            f3: float = default_field(metadata=meta(float))
            f4: str = default_field(metadata=meta(str))

        d = {"f1": 3, "f2": True, "f3": 2.4, "f4": "hello"}
        test_class = TestClass.from_dict(d)
        self.assertEqual(test_class.f1, 3)
        self.assertEqual(test_class.f2, True)
        self.assertAlmostEqual(test_class.f3, 2.4)
        self.assertEqual(test_class.f4, "hello")
        d2 = {"f1": 0, "f2": False, "f3": 0.0, "f4": ""}
        test_class = TestClass.from_dict(d2)
        self.assertEqual(test_class.f1, 0)
        self.assertEqual(test_class.f2, False)
        self.assertAlmostEqual(test_class.f3, 0.0)
        self.assertEqual(test_class.f4, "")

    def test_validator_for_wrong_type(self):
        @convertibleclass
        class TestClass:
            f1: int = 0
            f2: str = default_field()

        d = {"f1": 12, "f2": {"wrong": "dict"}}
        with self.assertRaises(Exception):
            TestClass.from_dict(d)

    def test_validate_for_class(self):
        @convertibleclass
        class TestClass:
            f1: int = 0
            f2: str = default_field()

            @classmethod
            def validate(cls, test_class):
                if len(test_class.f2) != 0:
                    raise Exception("wrong string length")

        d = {"f1": 12, "f2": "str"}
        with self.assertRaises(Exception):
            TestClass.from_dict(d)

    def test_required_for_field(self):
        @convertibleclass
        class TestClass:
            f1: int = 0
            f2: str = default_field(metadata=meta(required=True))

        d = {"f1": 12}
        with self.assertRaises(Exception):
            TestClass.from_dict(d)

    def test_list_of_classes_in_a_nested_class(self):
        @convertibleclass
        class NestedNestedTestClass:
            f3: str = default_field(metadata=meta(required=True))

        @convertibleclass
        class NestedTestClass:
            f2: list[NestedNestedTestClass] = default_field(
                metadata=meta(required=True)
            )
            nf1: datetime = default_field(
                metadata=meta(
                    value_to_field=lambda n: datetime.strptime(n, "%Y-%m-%d")
                ),
            )

        @convertibleclass
        class TestClass:
            f1: NestedTestClass = default_field(metadata=meta(required=True))

        d = {
            "f1": {
                "f2": [{"f3": "some text 1"}, {"f3": "some text 2"}],
                "nf1": "1980-01-01",
            }
        }
        result = TestClass.from_dict(d)
        self.assertIsNotNone(result.f1)
        self.assertIsNotNone(result.f1.f2)
        self.assertEqual(result.f1.f2[0].f3, "some text 1")
        self.assertEqual(result.f1.f2[1].f3, "some text 2")
        self.assertEqual(result.f1.nf1, datetime.strptime("1980-01-01", "%Y-%m-%d"))

    def test_list_of_required_ints_in_a_nested_class(self):
        @convertibleclass
        class NestedTestClass:
            f2: list[int] = default_field(metadata=meta(required=True))

        @convertibleclass
        class TestClass:
            f1: NestedTestClass = default_field(metadata=meta(required=True))

        d = {"f1": {"f2": [987, 654, 321]}}
        result = TestClass.from_dict(d)
        self.assertEqual(result.f1.f2[0], 987)
        self.assertEqual(result.f1.f2[1], 654)
        self.assertEqual(result.f1.f2[2], 321)

    def test_simple_class_with_enum(self):
        @convertibleclass
        class TestClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            f1: int = 0
            f2: str = default_field(metadata=meta(validate_len(min=1)))
            f3: bool = False
            f4: float = 0.0
            f5: TestEnum = TestEnum.T1

        d = {"f1": 12, "f2": "str", "f3": True, "f4": 12.12, "f5": "T2"}
        test_class = TestClass.from_dict(d)
        self.assertEqual(test_class.f1, 12)
        self.assertEqual(test_class.f2, "str")
        self.assertEqual(test_class.f3, True)
        self.assertEqual(test_class.f4, 12.12)
        self.assertEqual(test_class.f5, TestClass.TestEnum.T2)

    def test_complex_class(self):
        @convertibleclass
        class TestNestedClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            nf1: str = default_field(metadata=meta(validate_len(min=1)))
            nf2: TestEnum = TestEnum.T1
            nlf1: list[TestEnum] = default_field()
            nlf2: list[str] = default_field()

        @convertibleclass
        class TestClass:
            f1: int = field(default=0)
            f2: str = default_field()
            f3: bool = field(default=False)
            f4: float = field(default=0.0)
            f5: list[TestNestedClass] = default_field()
            f6: TestNestedClass = default_field()

        d = {
            "f1": 12,
            "f2": "str",
            "f3": True,
            "f4": 12.12,
            "f5": [
                {"nf1": "strnf1", "nf2": "T1"},
                {"nf1": "strnf2", "nf2": "T2", "nlf1": ["T1", "T2"], "nlf2": ["F1"]},
            ],
            "f6": {"nf1": "str123", "nf2": "T2"},
        }
        test_object = TestClass.from_dict(d)
        self.assertEqual(test_object.f1, 12)
        self.assertEqual(test_object.f2, "str")
        self.assertEqual(test_object.f3, True)
        self.assertEqual(test_object.f4, 12.12)
        self.assertEqual(len(test_object.f5), 2)
        self.assertTrue(isinstance(test_object.f5[0], TestNestedClass))
        self.assertEqual(test_object.f5[0].nf1, "strnf1")
        self.assertEqual(test_object.f5[0].nf2, TestNestedClass.TestEnum.T1)
        self.assertTrue(isinstance(test_object.f5[1], TestNestedClass))
        self.assertEqual(test_object.f5[1].nf1, "strnf2")
        self.assertEqual(test_object.f5[1].nf2, TestNestedClass.TestEnum.T2)
        self.assertEqual(
            test_object.f5[1].nlf1,
            [TestNestedClass.TestEnum.T1, TestNestedClass.TestEnum.T2],
        )
        self.assertEqual(test_object.f5[1].nlf2, ["F1"])
        self.assertTrue(isinstance(test_object.f6, TestNestedClass))
        self.assertEqual(test_object.f6.nf1, "str123")
        self.assertEqual(test_object.f6.nf2, TestNestedClass.TestEnum.T2)
        with self.assertRaises(Exception) as _:
            # illegal enum value in list
            v = {
                "f1": 12,
                "f2": "str",
                "f3": True,
                "f4": 12.12,
                "f5": [
                    {"nf1": "strnf1", "nf2": "T1"},
                    {"nf1": "strnf2", "nf2": "T2", "nlf1": ["T1", "XX"]},
                ],
                "f6": {"nf1": "str123", "nf2": "T2"},
            }
            TestClass.from_dict(v)
        d2 = {"f1": 12, "f6": {"nf1": "str123"}}
        test_object2 = TestClass.from_dict(d2)
        self.assertIsNone(test_object2.f6.nlf1)

    def test_none_type_exception(self):
        @convertibleclass
        class TestClass:
            f2: str = default_field(metadata=meta(required=True))
            f1: int = 0
            f3: bool = False

        with self.assertRaises(Exception):
            TestClass.from_dict({"f1": 12, "f2": None, "f3": True})

    def test_simple_inheritance(self):
        @convertibleclass
        class TestParentClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            nf1: str = default_field(metadata=meta(validate_len(min=1)))
            nf2: TestEnum = TestEnum.T1

        @convertibleclass
        class TestChildClass(TestParentClass):
            f2: str = default_field(metadata=meta(validate_len(min=1)))
            f3: bool = None
            f4: float = None

        d = {"nf1": "strnf1", "nf2": "T1", "f2": "str", "f3": True, "f4": 12.12}
        test_class = TestChildClass.from_dict(d)
        self.assertEqual(test_class.f2, "str")
        self.assertTrue(test_class.f3)
        self.assertEqual(test_class.f4, 12.12)
        self.assertEqual(test_class.nf1, "strnf1")
        self.assertEqual(test_class.nf2, TestParentClass.TestEnum.T1)

    def test_inheritance_failure(self):
        @convertibleclass
        class TestParentClass:
            class TestEnum(Enum):
                T1 = 1
                T2 = 2

            nf1: str = default_field(metadata=meta(validate_len(min=1)))
            nf2: TestEnum = TestEnum.T1

        @convertibleclass
        class TestChildClass(TestParentClass):
            f2: str = default_field(metadata=meta(validate_len(0, 0)))
            f3: bool = None
            f4: float = None

        d = {"nf1": "", "nf2": "T1", "f2": "str", "f3": True, "f4": 12.12}
        with self.assertRaises(Exception):
            TestChildClass.from_dict(d)
        d = {"nf1": "nf1", "nf2": "T1", "f2": "dasf", "f3": True, "f4": 12.12}
        with self.assertRaises(Exception):
            TestChildClass.from_dict(d)

    def test_list_of_ints_field(self):
        @convertibleclass
        class TestClass:
            f: list[int] = default_field()

        tc = TestClass.from_dict({"f": [1, 2, 3]})
        self.assertEqual(tc.f, [1, 2, 3])

    def test_list_of_strings_field(self):
        @convertibleclass
        class TestClass:
            f: list[str] = default_field()

        tc = TestClass.from_dict({"f": ["a", "b", "c"]})
        self.assertEqual(tc.f, ["a", "b", "c"])

    def test_failure_str_to_list_of_strings_field(self):
        @convertibleclass
        class TestClass:
            f: list[str] = default_field()

        with self.assertRaises(Exception):
            _ = TestClass.from_dict({"f": "test"})

    def test_str_convertibleclass_field(self):
        """Test with field type "ClassName" (str) where ClassName is a registered
        DomainModel. ClassName must be given as a string when nesting the
        class itself due to a Python 3.7.1 bug that prevents the use of
        'from __future__ import annotations'. See shared/domain_model.py for details.
        """

        @convertibleclass
        class TestClass:
            name: str = default_field()
            f: "TestClass" = default_field()

        nested_tc = {"name": "Nested TestClass"}
        tc = TestClass.from_dict({"name": "Parent TestClass", "f": nested_tc})
        self.assertEqual(tc.f.name, "Nested TestClass")

    def test_list_str_convertibleclass_field(self):
        """Test with field type ["ClassName"] (list[str]) where ClassName is a registered
        DomainModel. ClassName must be given as a string when nesting the
        class itself due to a Python 3.7.1 bug that prevents the use of
        'from __future__ import annotations'. See shared/domain_model.py for details.
        """

        @convertibleclass
        class TestClass:
            name: str = default_field()
            f: list["TestClass"] = default_field()

        nested_tc = {"name": "Nested TestClass"}
        tc = TestClass.from_dict({"name": "Parent TestClass", "f": [nested_tc]})
        self.assertEqual(tc.f[0].name, "Nested TestClass")


class HelpersFunctionTestCase(unittest.TestCase):
    def test_is_list_simple_list(self):
        field_value = ["str"]
        field_type = list
        self.assertTrue(is_list_field(field_type, field_value))

    def test_is_not_list_field_value_str_type_list(self):
        field_value = "str"
        field_type = list
        self.assertFalse(is_list_field(field_type, field_value))

    def test_is_not_list_dict(self):
        field_value = {"val": "str"}
        field_type = dict
        self.assertFalse(is_list_field(field_type, field_value))

    def test_is_list_generic_list(self):
        field_value = ["str"]
        field_type = list
        self.assertTrue(is_list_field(field_type, field_value))


class SetFieldValueTestCase(unittest.TestCase):
    @convertibleclass
    class TestClass:
        name: str = default_field(metadata=meta(value_to_field=lambda x: x.upper()))

    def test_set_value(self):
        test_instance = self.TestClass()
        test_instance.set_field_value("name", "string_that_should_be_caps")

        self.assertEqual("STRING_THAT_SHOULD_BE_CAPS", test_instance.name)

    def test_set_value_wrong_field(self):
        test_instance = self.TestClass()
        with self.assertRaises(ConvertibleClassValidationError):
            test_instance.set_field_value("WRONG", "")


class ResetAttributesTestCase(unittest.TestCase):
    @convertibleclass
    class TestClass:
        NAME = "name"

        name: str = field(default="TestName")

    def test_reset_attributes(self):
        cls = self.TestClass(name="ActualName")
        cls.reset_attributes([self.TestClass.NAME])
        self.assertEqual("TestName", cls.name)

    def test_failure_reset_attributes_no_such_field(self):
        cls = self.TestClass(name="ActualName")
        with self.assertRaises(AttributeError):
            cls.reset_attributes(["test"], raise_error=True)

    def test_success_reset_attributes_no_such_field_raise_error_false(self):
        cls = self.TestClass(name="ActualName")
        cls.reset_attributes(["test"])
        self.assertEqual("ActualName", cls.name)


if __name__ == "__main__":
    unittest.main()
