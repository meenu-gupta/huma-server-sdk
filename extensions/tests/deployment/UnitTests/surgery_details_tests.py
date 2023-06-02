from unittest import TestCase

from extensions.authorization.models.user import UserSurgeryDetails
from extensions.deployment.models.deployment import (
    Deployment,
    SurgeryDetails,
    SurgeryDetail,
    SurgeryDetailItem,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class SurgeryDetailsTestCase(TestCase):
    def setUp(self) -> None:
        self.deployment = Deployment.from_dict(
            {
                Deployment.SURGERY_DETAILS: {
                    SurgeryDetails.OPERATION_TYPE: {
                        SurgeryDetail.DISPLAY_STRING: "Test1",
                        SurgeryDetail.PLACE_HOLDER: "Test1",
                        SurgeryDetail.ITEMS: [
                            {
                                SurgeryDetailItem.KEY: "testKey",
                                SurgeryDetailItem.VALUE: "testValue",
                                SurgeryDetailItem.ORDER: 0,
                            }
                        ],
                    }
                }
            }
        )

    def test_success_validate_user_surgery_details_callback(self):
        operation_key = UserSurgeryDetails.OPERATION_TYPE
        implant_key = UserSurgeryDetails.IMPLANT_TYPE
        test_cases = [
            ({operation_key: "testKey"}, 0),  # (body, errors_length)
            ({operation_key: "wrongKey"}, 1),
            ({operation_key: "wrongKey", implant_key: "none"}, 2),
            ({operation_key: "testKey", implant_key: "none"}, 1),
        ]
        for test_data, errors_length in test_cases:
            errors = self.deployment.surgeryDetails.validate_input(test_data)
            self.assertEqual(errors_length, len(errors))

    def test_success_validate_surgery_detail_item(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SurgeryDetailItem.from_dict(
                {
                    SurgeryDetailItem.KEY: "testKey",
                    SurgeryDetailItem.VALUE: "testValue",
                    SurgeryDetailItem.ORDER: -1,
                }
            )
