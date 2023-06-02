from extensions.module_result.models.primitives import Lysholm, Tegner
from extensions.tests.module_result.IntegrationTests.test_samples import common_fields
from extensions.tests.module_result.UnitTests.primitives_tests import (
    PrimitiveTestCase,
    COMMON_FIELDS,
)


def lysholm_primitive():
    primitive_dict = {
        **common_fields(),
        Lysholm.LIMP: 1,
        Lysholm.CANE_OR_CRUTCHES: 10,
        Lysholm.LOCKING_SENSATION: 10,
        Lysholm.GIVING_WAY_SENSATION: 10,
        Lysholm.SWELLING: 10,
        Lysholm.CLIMBING_STAIRS: 10,
        Lysholm.SQUATTING: 10,
        Lysholm.PAIN: 10,
    }

    primitive_dict.update(COMMON_FIELDS)

    return primitive_dict


class LysholmPrimitiveTestCase(PrimitiveTestCase):
    def test_success_create(self):
        primitive = Lysholm.create_from_dict(lysholm_primitive(), name="Lysholm")
        self.assertIsNotNone(primitive)

    def test_failure_without_required_fields(self):
        required_fields = {
            Lysholm.LIMP,
            Lysholm.CANE_OR_CRUTCHES,
            Lysholm.LOCKING_SENSATION,
            Lysholm.GIVING_WAY_SENSATION,
            Lysholm.SWELLING,
            Lysholm.CLIMBING_STAIRS,
            Lysholm.SQUATTING,
            Lysholm.PAIN,
        }

        for field in required_fields:
            data = lysholm_primitive()
            del data[field]
            self._assert_convertible_validation_err(Lysholm, data)


def tegner_primitive():
    primitive_dict = {
        **common_fields(),
        Tegner.ACTIVITY_LEVEL_BEFORE: 10,
        Tegner.ACTIVITY_LEVEL_CURRENT: 10,
    }

    primitive_dict.update(COMMON_FIELDS)

    return primitive_dict


class TegnerPrimitiveTestCase(PrimitiveTestCase):
    def test_success_create(self):
        primitive = Tegner.create_from_dict(tegner_primitive(), name="Tegner")
        self.assertIsNotNone(primitive)

    def test_failure_without_required_fields(self):
        required_fields = {
            Tegner.ACTIVITY_LEVEL_BEFORE,
            Tegner.ACTIVITY_LEVEL_CURRENT,
        }

        for field in required_fields:
            data = tegner_primitive()
            del data[field]
            self._assert_convertible_validation_err(Lysholm, data)
