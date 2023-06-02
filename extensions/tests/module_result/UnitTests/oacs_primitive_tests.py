from extensions.module_result.models.primitives import OACS
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)


def oacs_primitive():

    primitive_dict = {**common_fields(), OACS.OACS_SCORE: -10}

    primitive_dict.update(COMMON_FIELDS)

    return primitive_dict


class OACSPrimitiveTestCase(PrimitiveTestCase):
    def test_success_create(self):
        primitive_dict = oacs_primitive()
        try:
            primitive = OACS.create_from_dict(oacs_primitive(), name="OACS")
        except Exception:
            self.fail()
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.oacsScore, primitive_dict[OACS.OACS_SCORE])
