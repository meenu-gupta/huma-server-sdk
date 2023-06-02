import unittest
from unittest.mock import MagicMock, patch

from freezegun import freeze_time

from extensions.module_result.modules.ecg_module.service.ecg_healthkit_service import (
    ECGHealthKitService,
)


class MockUser:
    instance = MagicMock()
    id = 1


class MockConfig:
    instance = MagicMock()
    defaultBucket = "first_bucket"
    storage = MagicMock(return_value=defaultBucket)
    server = MagicMock(return_value=storage)


class ECGHealthKitPDFUtilsTestCase(unittest.TestCase):
    @patch(
        "extensions.module_result.modules.ecg_module.service.ecg_healthkit_service.generate_ecg_pdf"
    )
    @patch(
        "extensions.module_result.modules.ecg_module.service.ecg_healthkit_service.upload_ecg_to_bucket"
    )
    @freeze_time("2012-01-01")
    def test_success_generate_ecg_pdf(self, upload_ecg, gen_ecg_pdf):
        data = [1.4, 5.6, 7.2]
        avg_bpm = 110.3
        time = "2012-01-01T00:00:00Z"
        config = MockConfig()
        classification = "classification_data"
        file_storage = MagicMock()
        service = ECGHealthKitService(config=config, file_storage=file_storage)
        user = MockUser()
        service.generate_and_save_ecg_pdf_to_bucket(
            user=user,
            data=data,
            avg_bpm=avg_bpm,
            time=time,
            classification=classification,
        )
        gen_ecg_pdf.assert_called_with(user, data, avg_bpm, time, classification)
        upload_ecg.assert_called_with(
            file_storage,
            config.server.storage.defaultBucket,
            "user/1/ECGHealthKit/2012-01-01T00:00:00Z.pdf",
            gen_ecg_pdf(),
        )


if __name__ == "__main__":
    unittest.main()
