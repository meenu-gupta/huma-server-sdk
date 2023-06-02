from extensions.module_result.models.primitives import (
    IKDC,
    Symptoms,
    SportsActivity,
    KneeFunction,
)
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)


def ikdc_primitive():
    symptoms = {
        Symptoms.PAIN_ACTIVITY: 3,
        Symptoms.PAIN_HISTORY: 3,
        Symptoms.PAIN_SEVERITY: 3,
        Symptoms.STIFFNESS_HISTORY: 3,
        Symptoms.SWELLING_ACTIVITY: 3,
        Symptoms.GIVE_WAY_LOCK: 1,
        Symptoms.GIVE_WAY_ACTIVITY: 3,
    }
    sports_activity = {
        SportsActivity.HIGHEST_LEVEL: 3,
        SportsActivity.STAIRS_UP: 3,
        SportsActivity.STAIRS_DOWN: 3,
        SportsActivity.KNEEL: 3,
        SportsActivity.SQUAT: 3,
        SportsActivity.SIT: 1,
        SportsActivity.RISE: 3,
        SportsActivity.RUN: 3,
        SportsActivity.JUMP_AND_LAND: 3,
        SportsActivity.STOP_AND_START: 3,
    }

    knee_function = {KneeFunction.PRIOR: 3, KneeFunction.CURRENT: 3}

    primitive_dict = {
        **common_fields(),
        IKDC.SYMPTOMS: symptoms,
        IKDC.SPORTS_ACTIVITY: sports_activity,
        IKDC.KNEE_FUNCTION: knee_function,
    }

    primitive_dict.update(COMMON_FIELDS)

    return primitive_dict


class IKDCPrimitiveTestCase(PrimitiveTestCase):
    def test_success_create(self):
        try:
            primitive = IKDC.create_from_dict(ikdc_primitive(), name="IKDC")
        except Exception:
            self.fail()
        self.assertIsNotNone(primitive)
