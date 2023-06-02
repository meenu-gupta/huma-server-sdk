from datetime import date, datetime
from unittest import TestCase

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.export_deployment.pdf_report._cover_page import CoverPage, Field

now = datetime.utcnow()
now_str = now.strftime("%d %b %Y")
start_date_of_report = now.strftime("%d %b %Y")


class CoverLetterPageTestCase(TestCase):
    def test_get_context(self):
        test_user = self._get_user()
        page = CoverPage(
            None,
            test_user,
            Deployment(name="Test Deployment"),
            now,
            now,
        )
        context = page.get_context()
        expected_context = {
            "title": "Summary Health Report",
            "fields": [
                Field("Patient", "Tester Test"),
                Field("Deployment", "Test Deployment"),
                Field("Date Period", f"{start_date_of_report} - {now_str}"),
                Field("Email", "test@user.com"),
                Field("Gender", "Male"),
                Field("DOB", "05 Oct 1990"),
                Field("Height", "185 cm"),
            ],
        }
        self.assertEqual(expected_context, context)

    def test_get_context_no_dob(self):
        test_user = self._get_user()
        test_user.dateOfBirth = None
        page = CoverPage(
            None,
            test_user,
            Deployment(name="Test Deployment"),
            now,
            now,
        )
        context = page.get_context()
        expected_context = {
            "title": "Summary Health Report",
            "fields": [
                Field("Patient", "Tester Test"),
                Field("Deployment", "Test Deployment"),
                Field("Date Period", f"{start_date_of_report} - {now_str}"),
                Field("Email", "test@user.com"),
                Field("Gender", "Male"),
                Field("DOB", None),
                Field("Height", "185 cm"),
            ],
        }
        self.assertEqual(expected_context, context)

    def test_get_context_no_height(self):
        test_user = self._get_user()
        test_user.height = None
        page = CoverPage(
            None,
            test_user,
            Deployment(name="Test Deployment"),
            now,
            now,
        )
        context = page.get_context()
        expected_context = {
            "title": "Summary Health Report",
            "fields": [
                Field("Patient", "Tester Test"),
                Field("Deployment", "Test Deployment"),
                Field("Date Period", f"{start_date_of_report} - {now_str}"),
                Field("Email", "test@user.com"),
                Field("Gender", "Male"),
                Field("DOB", "05 Oct 1990"),
                Field("Height", None),
            ],
        }
        self.assertEqual(expected_context, context)

    def _get_user(self):
        dob = date(year=1990, month=10, day=5)
        return User(
            email="test@user.com",
            givenName="Tester",
            familyName="Test",
            dateOfBirth=dob,
            gender=User.Gender.MALE,
            height=185,
            timezone="UTC",
        )
