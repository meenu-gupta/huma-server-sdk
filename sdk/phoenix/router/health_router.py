from flask import Blueprint, Response, Flask, jsonify
from pymongo.database import Database
from redis import Redis

from sdk.common.adapter.mongodb.mongodb_utils import db_is_accessible
from sdk.common.adapter.redis.redis_utils import cache_is_accessible
from sdk.common.utils import inject

api = Blueprint("health_route", __name__, url_prefix="/health")


# @api.route("/routes")
def list_routes():
    app = inject.instance(Flask)
    return jsonify(["%s" % rule for rule in app.url_map.iter_rules()]), 200


@api.route("/ready", methods=["GET", "POST"])
def ready():
    if not db_is_accessible(inject.instance(Database)):
        return Response("Inaccessible database.", 400, content_type="text/html")

    if not cache_is_accessible(inject.instance(Redis)):
        return Response("Inaccessible Cache.", 400, content_type="text/html")

    return Response("Ok.", 200, content_type="text/html")


@api.route("/live", methods=["GET", "POST"])
def live():
    if not db_is_accessible(inject.instance(Database)):
        return Response("Inaccessible database.", 400, content_type="text/html")

    if not cache_is_accessible(inject.instance(Redis)):
        return Response("Inaccessible Cache.", 400, content_type="text/html")

    return Response("Ok.", 200, content_type="text/html")
