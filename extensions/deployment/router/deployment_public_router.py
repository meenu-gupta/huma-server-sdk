import io
import json
from dataclasses import field

import qrcode
from flasgger import swag_from
from flask import Blueprint, jsonify, request, send_file
from flask_limiter import Limiter
from qrcode.image.pil import PilImage

from extensions.deployment.service.deployment_service import DeploymentService
from sdk import convertibleclass
from sdk.auth.validators import validate_project_and_client_id
from sdk.common.constants import SWAGGER_DIR
from sdk.common.utils import inject
from sdk.common.utils.convertible import required_field, default_field, meta
from sdk.common.utils.validators import (
    remove_none_values,
    default_version_meta,
    not_empty,
)
from sdk.phoenix.config.server_config import PhoenixServerConfig
from sdk.versioning.models.version_field import VersionField

api = Blueprint("deployment_public_route", __name__, url_prefix="/api/public/v1beta")


@api.before_app_first_request
def init_limit():
    limiter = inject.instance(Limiter)
    limiter.limit("4/minute")(api)


@api.route("/activation-code/<code>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/check_activation_code.yml")
def check_activation_code(code):
    (
        deployment,
        code_type,
        care_plan_group_id,
    ) = DeploymentService().retrieve_deployment_with_code(code)

    if not deployment:
        return None, 400

    return (
        jsonify(
            remove_none_values(
                {
                    "type": code_type,
                    "privacyPolicyUrl": deployment.privacyPolicyUrl,
                    "eulaUrl": deployment.eulaUrl,
                    "termAndConditionUrl": deployment.termAndConditionUrl,
                    "mfaRequired": deployment.mfaRequired,
                    "security": deployment.security,
                }
            )
        ),
        201,
    )


@convertibleclass
class Region:
    BUCKET = "bucket"
    CLIENT_ID = "clientId"
    PROJECT_ID = "projectId"
    END_POINT_URL = "endPointUrl"
    MINIMUM_VERSION = "minimumVersion"
    BUCKET_REGION = "bucketRegion"
    COUNTRY_CODE = "countryCode"
    STAGE = "stage"

    bucket: str = required_field()
    bucketRegion: str = field(default="us-west-2")
    clientId: str = required_field(metadata=meta(not_empty))
    countryCode: str = field(default="gb")
    endPointUrl: str = required_field()
    projectId: str = required_field(metadata=meta(not_empty))
    stage: str = field(default="DYNAMIC")
    minimumVersion: VersionField = default_field(metadata=default_version_meta())

    def to_qrcode(self):
        return qrcode.make(json.dumps(self.to_dict(include_none=False)))

    @classmethod
    def validate(cls, instance):
        validate_project_and_client_id(instance.clientId, instance.projectId)


@api.route("/region", methods=["GET"])
def get_region():
    args = request.args or {}
    client_id = args.get("clientId")
    response_type = args.get("type")
    if not client_id:
        return "Not Found", 404

    config: PhoenixServerConfig = inject.instance(PhoenixServerConfig)
    data = {
        Region.BUCKET: config.server.storage.defaultBucket,
        Region.CLIENT_ID: client_id,
        Region.PROJECT_ID: config.server.project.id,
        Region.END_POINT_URL: request.host_url.replace("http://", "https://", 1),
    }
    client = config.server.project.get_client_by_id(client_id)
    if client and client.minimumVersion:
        data.update({Region.MINIMUM_VERSION: client.minimumVersion})

    region = Region.from_dict(data)
    if response_type == "qrCode":
        qr_code: PilImage = region.to_qrcode()
        output = io.BytesIO()
        qr_code.save(output, format="PNG")
        output.seek(0, 0)
        return send_file(output, mimetype="image/png")
    else:
        return jsonify(region.to_dict(include_none=False)), 200
