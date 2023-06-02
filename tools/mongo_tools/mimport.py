#!/usr/bin/env python
import logging
import os
import sys
import fire
import pymongo
from pymongo.errors import PyMongoError

from sdk.common.utils.url_utils import clean_password_from_url

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from sdk.common.utils.file_utils import load_mongo_dump_file

logging.basicConfig(level=logging.DEBUG)


class MongoImport(object):
    logger = logging.getLogger(__name__)

    def __init__(
        self, database, input, url="localhost:27017",
    ):
        self.database = database
        self.input = input
        self.url = url

    def json(self):
        # ~~~~~~~~
        # connecting to mongo
        mongodb_db_client = pymongo.MongoClient(
            self.url, serverSelectionTimeoutMS=10 * 1000
        )

        # testing the connection before connecting
        db = mongodb_db_client[self.database]
        result = db.command("ping").get("ok")

        safe_url = clean_password_from_url(self.url)

        if result != 1.0:
            raise PyMongoError(f"can not connect to {safe_url}")

        self.logger.info(f"mongodb client has been connected {safe_url}")

        load_mongo_dump_file(self.input, db)


if __name__ == "__main__":
    fire.Fire(MongoImport)

    """
    How to run
    $ ./mimport --database phoenix_born --input ./test.json - json
    """
