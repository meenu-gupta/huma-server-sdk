import unittest
from datetime import datetime

from extensions.authorization.models.user import User
from extensions.module_result.modules.bmi import BMIModule
from extensions.module_result.models.primitives import Weight, Primitive, BMI
from sdk.common.exceptions.exceptions import InvalidRequestException

TEST_DEPLOYMENT_ID = "5e8f0c74b50aa9656c34789c"
TEST_USER_ID = "5e8f0c74b50aa9656c34789a"
USER_HEIGHT = 180
USER_WEIGHT = 80


def calculate_bmi(weight, height):
    height = height / 100
    return round(weight / (height * height), 2)


def user():
    return User(id=TEST_USER_ID, height=USER_HEIGHT)


def weight_primitive(value):
    return Weight(
        userId=TEST_USER_ID,
        moduleId="BMI",
        deviceName="iOS",
        deploymentId=TEST_DEPLOYMENT_ID,
        startDateTime=datetime.utcnow(),
        value=value,
    )


class BMIModuleTestCase(unittest.TestCase):
    def test_bmi_preprocess(self):
        module = BMIModule()
        primitives = [weight_primitive(USER_WEIGHT)]
        module.preprocess(primitives, user())

        self.assertEqual(len(primitives), 2)

        bmi = primitives[-1]
        self.assertTrue(isinstance(bmi, Primitive))
        self.assertEqual(bmi.value, calculate_bmi(USER_WEIGHT, USER_HEIGHT))

    def test_success_bmi_preprocess_minimum_weight(self):
        module = BMIModule()
        min_weight = 20
        primitives = [weight_primitive(min_weight)]
        module.preprocess(primitives, user())

        self.assertEqual(len(primitives), 2)

        bmi = primitives[-1]
        self.assertTrue(isinstance(bmi, Primitive))
        self.assertEqual(bmi.value, calculate_bmi(min_weight, USER_HEIGHT))

    def test_success_bmi_preprocess_maximum_weight(self):
        module = BMIModule()
        max_weight = 300
        primitives = [weight_primitive(max_weight)]
        module.preprocess(primitives, user())

        self.assertEqual(len(primitives), 2)

        bmi = primitives[-1]
        self.assertTrue(isinstance(bmi, Primitive))
        self.assertEqual(bmi.value, calculate_bmi(max_weight, USER_HEIGHT))

    def test_failure_creating_bmi_directly(self):
        module = BMIModule()
        weight = 75
        bmi_result = BMI(
            userId=TEST_USER_ID,
            moduleId="BMI",
            deviceName="iOS",
            deploymentId=TEST_DEPLOYMENT_ID,
            startDateTime=datetime.utcnow(),
            value=56.2,
        )
        primitives = [weight_primitive(weight), bmi_result]

        with self.assertRaises(InvalidRequestException):
            module.preprocess(primitives, user())
