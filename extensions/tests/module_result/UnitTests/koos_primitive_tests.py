import unittest

from extensions.module_result.models.primitives import KOOS, Primitive, WOMAC
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ID = "60fa9d91632c017458608307"


class KoosPrimitiveTestCase(unittest.TestCase):
    @staticmethod
    def _sample_koos() -> dict:
        keys = KOOS().__annotations__.keys()
        data = {k: 5.0 for k in keys}
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            **data,
        }

    def test_success_create_koos_primitive(self):
        data = self._sample_koos()
        try:
            KOOS.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missing_required_fields(self):
        required_fields = [
            KOOS.SYMPTOMS_SCORE,
            KOOS.SPORT_RECREATION_SCORE,
            KOOS.ADL_SCORE,
            KOOS.PAIN_SCORE,
            KOOS.QUALITY_OF_LIFE_SCORE,
        ]
        for field in required_fields:
            data = self._sample_koos()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                KOOS.from_dict(data)


class WomacPrimitiveTestCase(unittest.TestCase):
    @staticmethod
    def _sample_womac() -> dict:
        fields_to_ignore = [
            WOMAC.SYMPTOM_PREFIX,
            WOMAC.ADL_PREFIX,
            WOMAC.PAIN_PREFIX,
        ]
        keys = WOMAC().__annotations__.keys()
        data = {k: 5.0 for k in keys if k not in fields_to_ignore}
        return {
            **common_fields(),
            Primitive.USER_ID: SAMPLE_ID,
            Primitive.MODULE_ID: SAMPLE_ID,
            **data,
        }

    def test_success_create_womac_primitive(self):
        data = self._sample_womac()
        try:
            WOMAC.from_dict(data)
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_missing_required_fields(self):
        required_fields = [
            WOMAC.SYMPTOMS_SCORE,
            WOMAC.ADL_SCORE,
            WOMAC.PAIN_SCORE,
        ]
        for field in required_fields:
            data = self._sample_womac()
            data.pop(field)
            with self.assertRaises(ConvertibleClassValidationError):
                WOMAC.from_dict(data)


if __name__ == "__main__":
    unittest.main()
