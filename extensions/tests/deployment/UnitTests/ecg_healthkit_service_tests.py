import unittest
from unittest.mock import patch, MagicMock

from extensions.module_result.modules.ecg_module.pdf_utils import (
    generate_ecg_pdf,
    upload_ecg_to_bucket,
)


class MockFileStorage:
    instance = MagicMock()
    upload_file = MagicMock(return_value=MagicMock())


class ECGHealthKitServiceCase(unittest.TestCase):
    @patch("extensions.module_result.modules.ecg_module.pdf_utils.pdfkit")
    def test_success_generate_ecg_pdf(self, pdfkit):
        pdfkit.from_string.return_value = b""
        data = [1.4, 5.6, 7.2]
        avg_bpm = 120.5
        classification = "classification_data"
        user = MagicMock()
        time = "2012-01-01T00:00:00Z"
        generate_ecg_pdf(
            user=user,
            data=data,
            average_bpm=avg_bpm,
            time=time,
            classification=classification,
        )
        pdfkit.from_string.assert_called_once()

    @patch("extensions.module_result.modules.ecg_module.pdf_utils.BytesIO")
    def test_success_get_allowed_buckets(self, bytesIO):
        file_storage = MockFileStorage()
        bucket = "bucket_name"
        filename = "filename"
        file_data = b""
        bytesIO.return_value = MagicMock()
        upload_ecg_to_bucket(file_storage, bucket, filename, file_data)
        file_storage.upload_file.assert_called_with(
            bucket, filename, bytesIO(), len(file_data), "application/pdf"
        )

    @patch("extensions.module_result.modules.ecg_module.pdf_utils.render_template")
    @patch("extensions.module_result.modules.ecg_module.pdf_utils.pdfkit")
    def test_success_generate_ecg_pdf_user_no_db(self, pdfkit, render_template):
        pdfkit.from_string.return_value = b""
        data = [1.4, 5.6, 7.2]
        avg_bpm = 120.5
        classification = "classification_data"
        user = MagicMock()
        user.dateOfBirth = None
        user_name = "Some Name"
        user.get_full_name.return_value = user_name
        time = "2012-01-01T00:00:00Z"
        generate_ecg_pdf(
            user=user,
            data=data,
            average_bpm=avg_bpm,
            time=time,
            classification=classification,
        )
        render_template.assert_called_with(
            "ecg_healthkit_pdf_template.html",
            data=data,
            user_dob="",
            user_full_name=user_name,
            average_bpm=avg_bpm,
            time=time,
            classification=classification,
        )


if __name__ == "__main__":
    unittest.main()
