#!/usr/bin/env python
import json
import logging
import os
import sys

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from sdk.common.utils.url_utils import clean_password_from_url

import fire
import pymongo
from bson import json_util
from pymongo.errors import PyMongoError

logging.basicConfig(level=logging.DEBUG)


class MongoExport(object):
    logger = logging.getLogger(__name__)

    def __init__(
        self, database, output, collections: str, url="localhost:27027",
    ):
        self.database = database
        self.output = output
        if isinstance(collections, str):
            self.collections = [collections]
        else:
            self.collections = [c for c in collections]
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

        # read collection data and write to result var
        result = {}
        for cn in self.collections:
            collection = db.get_collection(cn)
            self.logger.info(f"retrieving documents of [{cn}]")
            cursor = collection.find({})
            docs = []
            for doc in cursor:
                docs.append(doc)
            result[cn] = docs

        with open(self.output, "w") as file:
            out = json.dumps(result, indent=4, default=json_util.default)
            file.write(out)
            file.close()

        # ls = json.loads(ls, object_hook=json_util.object_hook)
        self.logger.info(f"Output is writen of [{os.path.abspath(self.output)}]")


if __name__ == "__main__":
    fire.Fire(MongoExport)

    """
    How to run
    $ ./mexport --database phoenix_born --collections deployment,admin --output ./test.json - json
    """
