import unittest

from extensions.module_result.models.primitives.primitive_meta import PrimitiveMeta
from sdk.common.utils.convertible import ConvertibleClassValidationError


class PrimitiveMetaTestCase(unittest.TestCase):
    @staticmethod
    def _sample_data():
        return {
            PrimitiveMeta.NAME: "some_name",
            PrimitiveMeta.IS_DERIVED: False,
            PrimitiveMeta.CREATE_ARGUMENT: "some_args",
            PrimitiveMeta.CREATE_RESOLVER_NAME: "some_name",
        }

    def test_success_create_primitive_meta_primitive(self):
        data = self._sample_data()
        try:
            PrimitiveMeta.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_primitive_meta__no_required_fields(self):
        required_fields = [
            PrimitiveMeta.NAME,
            PrimitiveMeta.IS_DERIVED,
            PrimitiveMeta.CREATE_ARGUMENT,
            PrimitiveMeta.CREATE_RESOLVER_NAME,
        ]
        for field in required_fields:
            data = self._sample_data()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                PrimitiveMeta.from_dict(data)


if __name__ == "__main__":
    unittest.main()
