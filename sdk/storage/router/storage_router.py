from flasgger import swag_from
from flask import Blueprint, request, Response, send_file, make_response, jsonify, g
from werkzeug.utils import secure_filename

from sdk.common.constants import SWAGGER_DIR
from sdk.common.exceptions.exceptions import (
    BucketNotAllowedException,
    InvalidRequestException,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import StorageConfig, PhoenixServerConfig
from sdk.storage.use_case.storage_request_objects import (
    DownloadFileRequestObjectV1,
    GetSignedUrlRequestObjectV1,
    UploadFileRequestObject,
    DownloadFileRequestObject,
    GetSignedUrlRequestObject,
    UploadFileRequestObjectV1,
)
from sdk.storage.use_case.storage_use_cases import (
    DownloadFileUseCaseV1,
    GetSignedUrlUseCaseV1,
    UploadFileUseCase,
    DownloadFileUseCase,
    GetSignedUrlUseCase,
    UploadFileUseCaseV1,
)

URL_PREFIX = "/api/storage/v1beta"
api = Blueprint("storage_route", __name__, url_prefix=URL_PREFIX)

URL_PREFIX_V1 = "/api/storage/v1"
api_v1 = Blueprint("storage_v1_route", __name__, url_prefix=URL_PREFIX_V1)


def check_if_bucket_allowed(bucket: str, operation: str):
    config: StorageConfig = inject.instance(PhoenixServerConfig).server.storage
    if bucket not in config.allowedBuckets:
        raise BucketNotAllowedException(
            f'Bucket "{bucket}" is not allowed for "{operation}" operation'
        )


def verify_write(bucket: str, object_name: str = ""):
    check_if_bucket_allowed(bucket, "WRITE")


def verify_read(bucket: str, object_name: str = ""):
    check_if_bucket_allowed(bucket, "READ")


# file upload function
# Assuming the file/object/picture will be access in the body
# Assuming that the file will be contained in a variable called 'file'
# in the POST body.
#
@api.route("/upload/<bucket>", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/upload_file.yml")
def upload_file(bucket):
    verify_write(bucket)
    data = {
        **request.form,
        **request.files,
        DownloadFileRequestObject.BUCKET: bucket,
    }
    req = UploadFileRequestObject.from_dict(data)
    UploadFileUseCase().execute(req)
    return Response("Success", status=201)


# Given and bucket name and object name, download the object from minIO
#
@api.route("/download/<bucket>/<path:filename>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/download_file.yml")
def download_file(bucket, filename):
    verify_read(bucket, filename)
    req = DownloadFileRequestObject.from_dict(
        {
            DownloadFileRequestObject.BUCKET: bucket,
            DownloadFileRequestObject.FILENAME: filename,
        }
    )
    rsp = DownloadFileUseCase().execute(req)
    res = make_response(
        send_file(
            rsp.value.content,
            attachment_filename=filename,
            as_attachment=False,
            mimetype=rsp.value.contentType,
        )
    )
    res.headers["Content-Length"] = rsp.value.contentLength
    res.headers["Content-Security-Policy"] = "block-all-mixed-content"
    res.headers["Vary"] = "Origin"
    return res


@api.route("/signed/url/<bucket>/<path:filename>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_download_url.yml")
def retrieve_download_url(bucket, filename):
    verify_read(bucket, filename)
    req = GetSignedUrlRequestObject.from_dict(
        {
            GetSignedUrlRequestObject.BUCKET: bucket,
            GetSignedUrlRequestObject.FILENAME: filename,
            GetSignedUrlRequestObject.HOST: request.host,
        }
    )
    rsp = GetSignedUrlUseCase().execute(req)
    return rsp.value.url, 200


@api_v1.route("/upload", methods=["POST"])
@swag_from(f"{SWAGGER_DIR}/upload_file_v1.yml")
def upload_file_v1():
    req = UploadFileRequestObjectV1.from_dict(
        {
            **request.files,
            UploadFileRequestObjectV1.USER_ID: g.auth_user.id,
        }
    )
    rsp = UploadFileUseCaseV1().execute(req)
    return jsonify(rsp.value.to_dict()), 201


@api_v1.route("/download/<file_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/download_file_v1.yml")
def download_file_v1(file_id):
    req = DownloadFileRequestObjectV1.from_dict(
        {
            DownloadFileRequestObjectV1.FILE_ID: file_id,
        }
    )
    rsp = DownloadFileUseCaseV1().execute(req)
    res = make_response(
        send_file(
            rsp.value.content,
            attachment_filename=rsp.value.fileName,
            as_attachment=False,
            mimetype=rsp.value.contentType,
        )
    )
    res.headers["Content-Length"] = rsp.value.contentLength
    res.headers["Content-Security-Policy"] = "block-all-mixed-content"
    res.headers["Vary"] = "Origin"
    return res


@api_v1.route("/signed-url/<file_id>", methods=["GET"])
@swag_from(f"{SWAGGER_DIR}/retrieve_download_url_v1.yml")
def retrieve_download_url_v1(file_id):
    req = GetSignedUrlRequestObjectV1.from_dict(
        {
            GetSignedUrlRequestObjectV1.FILE_ID: file_id,
        }
    )
    rsp = GetSignedUrlUseCaseV1().execute(req)
    return jsonify(rsp.value.to_dict()), 200
