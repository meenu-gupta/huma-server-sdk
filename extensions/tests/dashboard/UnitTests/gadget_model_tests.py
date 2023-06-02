import unittest

from extensions.dashboard.models.dashboard import GadgetLink
from extensions.dashboard.models.gadget import GadgetId
from sdk.common.utils.convertible import ConvertibleClassValidationError


class GadgetModelTestCase(unittest.TestCase):
    def test_success_create_gadget(self):
        try:
            GadgetLink.from_dict(self._sample_gadget_dict())
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_negative_order(self):
        with self.assertRaises(ConvertibleClassValidationError):
            GadgetLink.from_dict(self._sample_gadget_dict(order=-1))

    def test_failure_wrong_size_format(self):
        sample_wrong_size_values = [
            "99x99",
            "11x10",
            "0x3",
            "aaa",
            "2345",
        ]
        for value in sample_wrong_size_values:
            with self.assertRaises(ConvertibleClassValidationError):
                GadgetLink.from_dict(self._sample_gadget_dict(size=value))

    @staticmethod
    def _sample_gadget_dict(order: int = 1, size: str = "2x2"):
        return {
            GadgetLink.SIZE: size,
            GadgetLink.ORDER: order,
            GadgetLink.ID: GadgetId.SIGNED_UP.value,
        }


if __name__ == "__main__":
    unittest.main()
