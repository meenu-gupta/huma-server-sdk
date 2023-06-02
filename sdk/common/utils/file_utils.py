import functools
import json
import logging
import textwrap
from pathlib import Path

from bson import json_util
from pymongo.database import Database

format_json = functools.partial(json.dumps, indent=2, sort_keys=True)
indent = functools.partial(textwrap.indent, prefix="  ")
logger = logging.getLogger(__name__)


def load_json_file(path):
    """
    Load a JSON document at path
    """
    p = Path(path)
    text = p.read_text()
    return json.loads(text)


def load_mongo_dump_file(file_path: str, database: Database):
    with open(file_path, "r") as file:
        collections = json.load(file, object_hook=json_util.object_hook)
        for (col, docs) in iter(collections.items()):
            for doc in docs:
                database[col].update_one(
                    {"_id": doc["_id"]}, {"$set": doc}, upsert=True
                )
            logger.info(f"{len(docs)} documents are written to collection {col}")
