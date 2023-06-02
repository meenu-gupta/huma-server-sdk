import datetime
import ipaddress
import json
import logging
from functools import wraps
from typing import Union, Hashable
import flask
from flask_limiter.util import get_ipaddr

from sdk.common.exceptions.exceptions import (
    InvalidRequestException,
    UnauthorizedException,
)
from sdk.common.utils.validators import utc_str_field_to_val, utc_date_to_str

logger = logging.getLogger(__name__)


def get_json_body(req: flask.Request) -> Union[list, dict]:
    try:
        body = req.json if hasattr(req, "json") else {}
    except Exception:
        body = {}
    return body or {}


def dump_request(req_uuid: str, req: flask.Request) -> dict:
    req_data = dict()
    req_data["logType"] = "RequestLog"
    req_data["request_id"] = req_uuid
    req_data["url"] = req.url
    req_data["method"] = req.method
    req_data["cookies"] = req.cookies
    req_data["json_body"] = get_json_body(req) or None
    req_data["headers"] = dict(req.headers)
    req_data["headers"].pop("Cookie", None)
    req_data["args"] = req.args
    req_data["form"] = req.form
    req_data["remote_addr"] = req.remote_addr
    files = []
    for name, fs in req.files.items():
        files.append(
            {
                "name": name,
                "filename": fs.filename,
                "filesize": fs.content_length,
                "mimetype": fs.mimetype,
                "mimetype_params": fs.mimetype_params,
            }
        )
    req_data["files"] = files
    return req_data


def dump_response(req_uuid: str, resp: flask.Response) -> dict:
    resp_data = dict()
    resp_data["logType"] = "ResponseLog"
    resp_data["request_id"] = req_uuid
    resp_data["status_code"] = resp.status_code
    resp_data["status"] = resp.status
    resp_data["headers"] = dict(resp.headers)
    content_type = resp.headers.get("Content-Type")
    if content_type == "application/json":
        try:
            resp_data["json_body"] = json.loads(resp.data)
        except Exception as e:
            logger.warning(repr(e))
    return resp_data


def get_request_json_dict_or_raise_exception(req: flask.Request) -> dict:
    body = req.json or {}
    if not body or not isinstance(body, dict):
        raise InvalidRequestException("Request json should be an object")

    return body


def validate_request_body_type_is_object(req: flask.Request) -> dict:
    body = req.json or {}
    if body and not isinstance(body, dict):
        raise InvalidRequestException("Request json should be an object")

    return body


def get_http_user_agent_from_request(req: flask.Request):
    user_agent = req.headers.get("User-Agent")

    if not user_agent:
        raise InvalidRequestException("User Agent is missing in headers")
    return user_agent


def get_request_json_list_or_raise_exception(req: flask.Request) -> list:
    body = req.json or []
    if not body or not isinstance(body, list):
        raise InvalidRequestException("Request json should be an array")

    return body


def private_ip_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not ipaddress.ip_address(get_ipaddr()).is_private:
            raise UnauthorizedException
        return f(*args, **kwargs)

    return inner


def get_key_value_from_request(req: flask.Request, key: Hashable):
    body = get_json_body(req)
    if isinstance(body, list):
        body = body[0]
    if isinstance(body, dict):
        return body.get(key)
    raise InvalidRequestException


def get_current_path_or_empty():
    try:
        return flask.request.path
    except RuntimeError:
        return ""


def get_current_url_rule_or_empty():
    try:
        return flask.request.url_rule
    except RuntimeError:
        return ""


class PhoenixJsonEncoder(flask.json.JSONEncoder):
    """To support a new conversion, add to the dict the conversion type and its converter"""

    _converters = {
        datetime.datetime: utc_str_field_to_val,
        datetime.date: utc_date_to_str,
    }

    def default(self, obj):
        converter = self._converters.get(type(obj))
        if converter:
            return converter(obj)

        return super(PhoenixJsonEncoder, self).default(obj)
