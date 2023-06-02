from extensions.module_result.models.primitives import OARS
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)


def oars_primitive():

    primitive_dict = {
        **common_fields(),
        OARS.OARS_SCORE: 50.7,
        OARS.PAIN_SCORE: 20.3,
        OARS.SLEEP_SCORE: 25.5,
        OARS.NAUSEA_SCORE: 67.0,
        OARS.MOBILITY_SCORE: 54.3,
    }

    primitive_dict.update(COMMON_FIELDS)

    return primitive_dict


class OARSPrimitiveTestCase(PrimitiveTestCase):
    def test_success_create(self):
        primitive_dict = oars_primitive()
        try:
            primitive = OARS.create_from_dict(oars_primitive(), name="OARS")
        except Exception:
            self.fail()
        self.assertIsNotNone(primitive)
        self.assertEqual(primitive.oarsScore, primitive_dict[OARS.OARS_SCORE])
        self.assertEqual(primitive.sleepScore, primitive_dict[OARS.SLEEP_SCORE])
        self.assertEqual(primitive.mobilityScore, primitive_dict[OARS.MOBILITY_SCORE])
        self.assertEqual(primitive.painScore, primitive_dict[OARS.PAIN_SCORE])
        self.assertEqual(primitive.nauseaScore, primitive_dict[OARS.NAUSEA_SCORE])
