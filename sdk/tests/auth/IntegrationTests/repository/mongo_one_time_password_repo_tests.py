import unittest
from pathlib import Path

import mongoengine.errors
from pymongo.database import Database

from sdk.common.adapter.mongodb.mongo_one_time_passowrd_repository import (
    MongoOneTimePasswordRepository,
)
from sdk.common.adapter.one_time_password_repository import (
    OneTimePasswordConfig,
    OneTimePassword,
)
from sdk.common.exceptions.exceptions import RateLimitException
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server, Adapters
from sdk.phoenix.di.components import read_config
from sdk.tests.application_test_utils.test_utils import (
    IntegrationTestCase,
    SDK_CONFIG_PATH,
)
from sdk.tests.test_case import SdkTestCase

ID = "+8618621329842"


def get_config(rate_limit: int):
    otp = OneTimePasswordConfig(rateLimit=rate_limit)
    return PhoenixServerConfig(
        server=Server(adapters=Adapters(oneTimePasswordRepo=otp))
    )


class MongoSimpleTestCase(IntegrationTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    def setUp(self):
        self.set_test_mongo_database(read_config(SDK_CONFIG_PATH))
        inject.clear_and_configure(lambda b: b.bind(Database, self.mongo_database))
        self.mongo_database.drop_collection("onetimepassword")

    def test_generate_password_and_verify(self):
        repo = MongoOneTimePasswordRepository(config=get_config(2))
        generated_pass = repo.generate_or_get_password(ID)
        verify_result = repo.verify_password(ID, generated_pass)
        self.assertTrue(verify_result)

    def test_generate_password_and_verify_second_time(self):
        repo = MongoOneTimePasswordRepository(config=get_config(2))
        generated_pass = repo.generate_or_get_password(ID)
        verify_result = repo.verify_password(ID, generated_pass)
        self.assertTrue(verify_result)

    def test_generate_password_and_twice_verify_not_possible(self):
        repo = MongoOneTimePasswordRepository(config=get_config(10))
        generated_pass = repo.generate_or_get_password(ID)
        wrong_pass = "111111"
        if wrong_pass == "111111":
            wrong_pass = "222222"
        verify_result = repo.verify_password(ID, wrong_pass)
        self.assertFalse(verify_result)
        verify_result = repo.verify_password(ID, generated_pass)
        self.assertTrue(verify_result)

    def test_wrong_password(self):
        repo = MongoOneTimePasswordRepository(config=get_config(2))
        generated_pass = repo.generate_or_get_password(ID)
        if generated_pass == "111111":
            generated_pass = "222222"
        else:
            generated_pass = "111111"
        verify_result = repo.verify_password(ID, generated_pass)
        self.assertFalse(verify_result)

    def test_wrong_id(self):
        repo = MongoOneTimePasswordRepository(config=get_config(2))
        verify_result = repo.verify_password(ID, "111111")
        self.assertFalse(verify_result)

    def test_rate_limit_for_specific_id(self):
        repo = MongoOneTimePasswordRepository(config=get_config(2))
        generated_pass = repo.generate_or_get_password(ID)
        if generated_pass == "111111":
            generated_pass = "222222"
        else:
            generated_pass = "111111"
        _ = repo.generate_or_get_password(ID)
        with self.assertRaises(Exception):
            _ = repo.generate_or_get_password(ID)

        # check code is removed from db after
        self.assertFalse(repo.verify_password(ID, generated_pass))

    def test_rate_limit_for_wrong_password(self):
        repo = MongoOneTimePasswordRepository(config=get_config(4))
        generated_pass = repo.generate_or_get_password(ID)
        if generated_pass == "111111":
            generated_pass = "222222"
        else:
            generated_pass = "111111"
        self.assertFalse(repo.verify_password(ID, generated_pass))
        self.assertFalse(repo.verify_password(ID, generated_pass))
        self.assertFalse(repo.verify_password(ID, generated_pass))
        with self.assertRaises(RateLimitException):
            _ = repo.verify_password(ID, generated_pass)

        # check code is removed from db after
        self.assertFalse(repo.verify_password(ID, generated_pass))


class MongoOneTimePasswordTestCase(SdkTestCase):
    components = []
    fixtures = [
        Path(__file__).parent.parent.joinpath("fixtures/onetimepassword_dump.json")
    ]
    _repo = None
    _request_dict = {
        OneTimePassword.IDENTIFIER: "test@gmail.com",
        OneTimePassword.PASSWORD: "pass",
        OneTimePassword.TYPE: "Verification",
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls._repo = MongoOneTimePasswordRepository(config=get_config(2))
        super(MongoOneTimePasswordTestCase, cls).setUpClass()

    def test_success_create_otp(self):
        reset_password_code = OneTimePassword.from_dict(
            {**self._request_dict, OneTimePassword.TYPE: "ResetPassword"}
        )
        self._repo.create_otp(reset_password_code)

    def test_failure_create_otp_with_same_identifier_and_type(self):
        verification_code = OneTimePassword.from_dict(self._request_dict)
        with self.assertRaises(mongoengine.errors.NotUniqueError):
            self._repo.create_otp(verification_code)


if __name__ == "__main__":
    unittest.main()
