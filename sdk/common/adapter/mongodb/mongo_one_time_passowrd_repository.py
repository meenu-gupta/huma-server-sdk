import random
import string
from datetime import datetime

from mongoengine import StringField, IntField, DateTimeField

from sdk.common.adapter.one_time_password_repository import (
    OneTimePasswordRepository,
    OneTimePassword,
)
from sdk.common.exceptions.exceptions import RateLimitException, ObjectDoesNotExist
from sdk.common.utils.inject import autoparams
from sdk.common.utils.mongo_utils import MongoPhoenixDocument
from sdk.common.utils.validators import remove_none_values
from sdk.phoenix.config.server_config import PhoenixServerConfig


class MongoOneTimePassword(MongoPhoenixDocument):
    DEFAULT_TYPE = "Verification"
    meta = {
        "collection": "onetimepassword",
        "indexes": [
            {
                "fields": [OneTimePassword.IDENTIFIER, OneTimePassword.TYPE],
                "unique": True,
            }
        ],
    }

    identifier = StringField()
    password = StringField()
    type = StringField(default=DEFAULT_TYPE)
    numberOfTry = IntField(min_value=1)
    createdAt = DateTimeField(default=datetime.utcnow)

    def increase_number_of_tries_or_die_and_delete(self, max_tries: int):
        if max_tries and self.numberOfTry >= max_tries:
            self.delete()
            raise RateLimitException

        self.numberOfTry += 1
        return self.save()


class MongoOneTimePasswordRepository(OneTimePasswordRepository):
    """
    How to configure it:
    > oneTimePasswordRepo:
    >   rateLimit: 2

    How to use it:
    > from sdk.common.adapter.one_time_password_repository import OneTimePasswordRepository
    > from sdk.common.utils import inject
    >
    > repo = inject.instance(OneTimePasswordRepository)
    > print(repo.generate_or_get_password("+8618621329842"))
    """

    DIGITS = string.digits
    LETTERS = string.ascii_letters

    @autoparams()
    def __init__(self, config: PhoenixServerConfig):
        self.config = config.server.adapters.oneTimePasswordRepo

    def generate_or_get_password(
        self,
        identifier: str,
        password_length: int = 6,
        include_characters: bool = False,
    ) -> str:
        doc = MongoOneTimePassword.objects(
            identifier=identifier, type=OneTimePassword.DEFAULT_TYPE
        ).first()
        if doc:
            doc.increase_number_of_tries_or_die_and_delete(self.config.rateLimit)
            return doc.password

        password = self.generate_password(password_length, include_characters)
        otp_dict = {
            OneTimePassword.IDENTIFIER: identifier,
            OneTimePassword.PASSWORD: password,
        }
        self.create_otp(OneTimePassword.from_dict(otp_dict))
        return password

    def generate_password(self, length, include_chars=False):
        chars = self.DIGITS + self.LETTERS if include_chars else self.DIGITS
        return "".join(random.choices(chars, k=length))

    def verify_password(
        self,
        identifier: str,
        password: str,
        code_type: str = MongoOneTimePassword.DEFAULT_TYPE,
        delete: bool = True,
    ) -> bool:
        doc = self.retrieve_otp(identifier, code_type)
        if not doc:
            return False

        doc.increase_number_of_tries_or_die_and_delete(self.config.rateLimit)
        if doc.password != password:
            return False
        if delete:
            doc.delete()
        return True

    def create_otp(self, otp: OneTimePassword):
        document = MongoOneTimePassword(**otp.to_dict(include_none=False)).save()
        return str(document.id)

    def retrieve_otp(self, identifier: str, code_type: str):
        docs = MongoOneTimePassword.objects(identifier=identifier, type=code_type)
        return docs.first()

    def delete_otp(self, identifier: str, code_type: str, code: str = None):
        query = {
            OneTimePassword.IDENTIFIER: identifier,
            OneTimePassword.TYPE: code_type,
            OneTimePassword.PASSWORD: code,
        }
        otp = MongoOneTimePassword.objects(**remove_none_values(query)).first()
        if not otp:
            raise ObjectDoesNotExist
        otp.delete()
