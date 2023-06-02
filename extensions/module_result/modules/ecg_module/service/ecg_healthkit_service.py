import datetime
import logging

from numbers import Number
from extensions.authorization.models.user import User
from extensions.common.s3object import S3Object
from extensions.exceptions import ECGPdfGenerationError
from extensions.module_result.modules.ecg_module.pdf_utils import (
    generate_ecg_pdf,
    upload_ecg_to_bucket,
)
from extensions.module_result.models.primitives import ECGHealthKit
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.utils.date_utils import get_dt_now_as_str
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class ECGHealthKitService:
    @autoparams()
    def __init__(
        self,
        config: PhoenixServerConfig,
        file_storage: FileStorageAdapter,
    ):
        self.config = config
        self.file_storage = file_storage

    def _get_default_bucket(self):
        return self.config.server.storage.defaultBucket

    def generate_and_save_ecg_pdf_to_bucket(
        self,
        user: User,
        data: list,
        avg_bpm: Number,
        time: datetime,
        classification: str,
    ) -> S3Object:
        bucket = self._get_default_bucket()
        dt_now = get_dt_now_as_str()
        filename = f"user/{user.id}/{ECGHealthKit.__name__}/{dt_now}.pdf"
        try:
            pdf = generate_ecg_pdf(user, data, avg_bpm, time, classification)
        except Exception:
            logger.error(f"ECG PDF was not generated for user {user.id}")
            raise ECGPdfGenerationError
        return upload_ecg_to_bucket(self.file_storage, bucket, filename, pdf)
