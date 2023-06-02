import functools
import json
import logging
import logging.config
import os
import time
from typing import OrderedDict

import yaml
from flask import has_request_context
from pythonjsonlogger import jsonlogger


class UTCFormatter(logging.Formatter):
    converter = time.gmtime
    default_msec_format = "%s.%03d"


def json_translate(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], OrderedDict):
        args[0]["level"] = args[0]["severity"] = args[0].get("levelname")
        if has_request_context():
            from flask import g

            if g.get("uuid") and not args[0].get("request_id"):
                args[0]["request_id"] = g.uuid

    return json.dumps(*args, **kwargs)


class SpecialJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            json_serializer=json_translate,
            json_encoder=json.JSONEncoder,
            *args,
            **kwargs,
        )


DEFAULT_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "utc": {
            "()": UTCFormatter,
            "format": "%(asctime)sZ %(levelname)s [%(name)s:%(funcName)s:%(lineno)s] %(message)s",
        },
        "json": {
            "format": "%(asctime)sZ %(levelname)s [%(name)s:%(funcName)s:%(lineno)s] %(message)s",
            "()": SpecialJsonFormatter,
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "utc",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"handlers": ["stdout"], "level": "INFO"},
    "loggers": {
        "geventwebsocket.handler": {"level": "WARN"},
        "waitress.handler": {"level": "WARN"},
        "celery": {"level": "WARN"},
        "celery.task": {"level": "WARN"},
        "celery.worker": {"level": "WARN"},
    },
}


@functools.lru_cache(maxsize=1)
def init_logging(debug: bool = False):
    """Set log level and formatter at root.  lru_cache means this function is called once per process"""
    log_config_file_name = os.getenv("LOG_CONFIG_YAML_FILE", None)
    if log_config_file_name is None:
        conf = DEFAULT_LOG_CONFIG
        if debug:
            conf["root"]["level"] = "DEBUG"
            conf["loggers"]["geventwebsocket.handler"]["level"] = "DEBUG"
            conf["loggers"]["waitress.handler"]["level"] = "DEBUG"
            conf["loggers"]["celery"]["level"] = "DEBUG"
            conf["loggers"]["celery.task"]["level"] = "DEBUG"
            conf["loggers"]["celery.worker"]["level"] = "DEBUG"
            logger = logging.getLogger("waitress")
            logger.setLevel(logging.DEBUG)

        if os.getenv("JSON_LOGGING_ENABLED", None):
            conf["handlers"]["stdout"]["formatter"] = "json"

        logging.config.dictConfig(conf)

        # get logger

        logging.debug("Logging initialized with default config")
        return

    # Otherwise, load and parse the log file
    with open(log_config_file_name, "r") as config_file:
        config_dict = yaml.load(config_file)
        logging.config.dictConfig(config_dict)
        logging.debug(f"Logging initialized with config from {log_config_file_name}")
