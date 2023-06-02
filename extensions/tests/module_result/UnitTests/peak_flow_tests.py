import math
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta

from extensions.authorization.models.user import User
from extensions.module_result.modules.peak_flow import PeakFlowModule
from extensions.module_result.models.primitives import PeakFlow

TEST_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_USER_ID = "5e8f0c74b50aa9656c34789c"
USER_HEIGHT = 180
USER_PEAK_FLOW_VALUE = 400
USER_GENDER = User.Gender.MALE
USER_DOB = datetime.utcnow() - relativedelta(years=32)
AUTHORIZATION_SERVICE_ROUTE = (
    "extensions.module_result.modules.peak_flow.AuthorizationService"
)


def user():
    return User(
        id=TEST_USER_ID, height=USER_HEIGHT, gender=USER_GENDER, dateOfBirth=USER_DOB
    )


def peak_flow_primitive(value):
    return PeakFlow(
        userId=TEST_USER_ID,
        moduleId="PeakFlow",
        deviceName="iOS",
        deploymentId=TEST_DEPLOYMENT_ID,
        startDateTime=datetime.utcnow(),
        value=value,
    )


class MockAuthService:
    retrieve_user_profile = MagicMock()
    retrieve_user_profile.return_value = user()


class PeakFlowModuleTestCase(unittest.TestCase):
    @patch(AUTHORIZATION_SERVICE_ROUTE, MockAuthService)
    def test_peak_flow_calculate(self):
        module = PeakFlowModule()
        peak_flow = peak_flow_primitive(USER_PEAK_FLOW_VALUE)
        module.calculate(peak_flow)
        test_user = user()
        is_equal = math.isclose(
            peak_flow.valuePercent,
            peak_flow.calculate_percent(
                test_user.gender,
                test_user.get_age(),
                test_user.height,
            ),
            rel_tol=1e-9,
            abs_tol=0.0,
        )
        self.assertTrue(is_equal)

    def test_multiple_value_peak_flow_calculate_percent(self):
        """
        expected_percentage values from https://www.omnicalculator.com/health/peak-flow
            and choose Ethnicity as Other
        """
        multiple_values = {
            "Test Case #1": {
                "gender": user().gender,
                "age": user().get_age(),
                "height": user().height,
                "origin_value": USER_PEAK_FLOW_VALUE,
                "expected_percentage": 65.798,
            },
            "Test Case #2": {
                "gender": User.Gender.FEMALE,
                "age": 71,
                "height": 177,
                "origin_value": 300,
                "expected_percentage": 74.69,
            },
            "Test Case #3": {
                "gender": User.Gender.MALE,
                "age": 44,
                "height": 155,
                "origin_value": 250,
                "expected_percentage": 50.38,
            },
            "Test Case #4": {
                "gender": User.Gender.MALE,
                "age": 23,
                "height": 170,
                "origin_value": 500,
                "expected_percentage": 83.73,
            },
        }

        for key, value in multiple_values.items():
            expected_percentage = value.pop("expected_percentage")
            primitive = PeakFlow(value=value.pop("origin_value"))
            self.assertAlmostEqual(
                expected_percentage,
                round(primitive.calculate_percent(**value), ndigits=2),
                places=2,
                msg=key,
            )
