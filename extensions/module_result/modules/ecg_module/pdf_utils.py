import datetime
import logging
from io import BytesIO
from numbers import Number

import pdfkit
from flask import render_template, Flask

from extensions.authorization.models.user import User
from extensions.common.s3object import S3Object
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter

app = Flask(__name__, template_folder="service/templates/")

logger = logging.getLogger(__name__)


def upload_ecg_to_bucket(
    file_storage: FileStorageAdapter, bucket: str, filename: str, file_data: bytes
) -> S3Object:
    file_storage.upload_file(
        bucket, filename, BytesIO(file_data), len(file_data), "application/pdf"
    )
    return S3Object(bucket=bucket, key=filename)


def generate_ecg_pdf(
    user: User, data: list, average_bpm: Number, time: datetime, classification: str
) -> bytes:

    options = {
        "page-size": "A3",
        "margin-top": "0.75in",
        "margin-right": "0.5in",
        "margin-bottom": "0.5in",
        "margin-left": "0.5in",
        "encoding": "UTF-8",
        "orientation": "Landscape",
        "enable-local-file-access": None,
    }

    with app.app_context():
        user_dob = user.dateOfBirth
        user_full_name = user.get_full_name()
        html = render_template(
            "ecg_healthkit_pdf_template.html",
            data=data,
            user_dob=user_dob or "",
            user_full_name=user_full_name,
            average_bpm=average_bpm,
            time=time,
            classification=classification,
        )
    return pdfkit.from_string(html, False, options=options)
