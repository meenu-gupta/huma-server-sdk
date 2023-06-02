from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.use_cases.sign_econsent_use_case import (
    SignEConsentUseCase,
)
from extensions.common.s3object import S3Object
from extensions.deployment.models.consent.consent import AdditionalConsentQuestion
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.router.deployment_requests import (
    CreateEConsentRequestObject,
    SignEConsentRequestObject,
)
from extensions.tests.shared.test_helpers import simple_econsent, simple_econsent_log
from sdk.celery.app import celery_app
from sdk.common.localization.utils import Language
from sdk.common.utils.common_functions_utils import get_full_name_for_signature
from sdk.common.utils.convertible import ConvertibleClassValidationError


USE_CASE_PATH = "extensions.authorization.use_cases.sign_econsent_use_case"
DEPLOYMENT_ID = "5ffea8e41d3eaea109cd0773"
USER_FULL_NAME = "John Smith"
TITLE_TRANSLATE = "hu_econsent_title"
ADDITIONAL_QUESTION_TRANSLATE_PREFIX = "hu_econsent_additional_question_{}"
YES_TRANSLATE = "hu_econsent_yes"
NO_TRANSLATE = "hu_econsent_no"


def translation_strings_simple_econsent() -> dict:
    val = simple_econsent()
    val["title"] = TITLE_TRANSLATE
    val["additionalConsentQuestions"][1][
        "text"
    ] = ADDITIONAL_QUESTION_TRANSLATE_PREFIX.format("1")
    val["additionalConsentQuestions"][0][
        "text"
    ] = ADDITIONAL_QUESTION_TRANSLATE_PREFIX.format("2")
    return val


class MockEConsentRepo(MagicMock):
    is_latest_econsent_signed = MagicMock()
    is_latest_econsent_signed.return_value = False
    retrieve_latest_econsent = MagicMock()
    retrieve_latest_econsent.return_value = EConsent.from_dict(
        translation_strings_simple_econsent()
    )
    create_econsent_log = MagicMock()
    create_econsent_log.return_value = "607d55188a0cdbe7fc1ff6e3"
    update_user_econsent_pdf_location = MagicMock()
    retrieve_log_count = MagicMock()
    retrieve_log_count.return_value = 0


def get_translations() -> dict:
    return {
        TITLE_TRANSLATE: "This is a title",
        ADDITIONAL_QUESTION_TRANSLATE_PREFIX.format("1"): "This is a question",
        ADDITIONAL_QUESTION_TRANSLATE_PREFIX.format("2"): "And another one",
        YES_TRANSLATE: "Ja",
        NO_TRANSLATE: "Nein",
    }


class MockAuthorizedUser(MagicMock):
    get_language = MagicMock()
    get_language.return_value = Language.EN

    @property
    def localization(self):
        return self.deployment.localizations

    @property
    def deployment(self):
        return Deployment(
            id=DEPLOYMENT_ID,
            econsent=EConsent.from_dict(translation_strings_simple_econsent()),
            localizations=get_translations(),
        )


class CreateEConsentRequestObjectTestCase(TestCase):
    def setUp(self):
        self.econsent = translation_strings_simple_econsent()

    def test_success_create(self):
        request_object = CreateEConsentRequestObject.from_dict(self.econsent)
        for key, val in self.econsent.items():
            field_val = getattr(request_object, key)

            if isinstance(
                field_val, (str, int, bool)
            ):  # compare base types (str, int, bool)
                self.assertEqual(val, field_val)

    def test_failure_create_no_enabled_field(self):
        self.econsent.pop("enabled", None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_no_title_field(self):
        self.econsent.pop("title", None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_no_overview_text_field(self):
        self.econsent.pop("overviewText", None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_no_contact_text_field(self):
        self.econsent.pop("contactText", None)
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_with_create_date(self):
        self.econsent.update(
            {CreateEConsentRequestObject.CREATE_DATE_TIME: "2020-12-31T00:00:00.000Z"}
        )
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_with_id(self):
        self.econsent.update(
            {CreateEConsentRequestObject.ID: "a733671100cd26d816eed39507"}
        )
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_with_invalid_format(self):
        self.econsent[EConsent.ADDITIONAL_CONSENT_QUESTIONS][0].update(
            {AdditionalConsentQuestion.FORMAT: "Invalid"}
        )
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)

    def test_failure_create_with_invalid_enabled(self):
        self.econsent[EConsent.ADDITIONAL_CONSENT_QUESTIONS][0].update(
            {AdditionalConsentQuestion.ENABLED: True}
        )
        with self.assertRaises(ConvertibleClassValidationError):
            CreateEConsentRequestObject.from_dict(self.econsent)


class SignEConsentRequestObjectTestCase(TestCase):
    def setUp(self):
        self.request_object = SignEConsentRequestObject(
            givenName="givenName",
            middleName="middleName",
            familyName="familyName",
            signature=S3Object(key="test.pdf", region="eu", bucket="bucket1"),
            userId="60640eec8464365dbd917f50",
            econsentId="60640eec8464365dbd917f50",
            sharingOption=1,
            deploymentId=DEPLOYMENT_ID,
            requestId="df04bf98eb8647769af4adc4f2905812",
            user=MockAuthorizedUser(),
            additionalConsentAnswers={
                "isDataSharedForFutureStudies": False,
                "isDataSharedForResearch": True,
            },
        )

    def test_success_sign(self):
        request_sample = self.request_object.to_dict(ignored_fields=("user",))
        for key, val in request_sample.items():
            field_val = getattr(self.request_object, key)
            if isinstance(field_val, (str, int, bool)) and type(field_val) is type(
                val
            ):  # compare base types (str, int, bool)
                self.assertEqual(val, field_val)

    def test_success_check_get_full_name(self):
        self.assertEqual(
            get_full_name_for_signature(
                given_name=self.request_object.givenName,
                family_name=self.request_object.familyName,
            ).upper(),
            self.request_object.get_full_name(),
        )

    def test_failure_create_with_pdf_location_field(self):
        request_sample = simple_econsent_log()
        pdf_location = S3Object.from_dict(
            {"key": "test.pdf", "region": "eu", "bucket": "bucket1"}
        )
        request_sample.update({SignEConsentRequestObject.PDF_LOCATION: pdf_location})
        with self.assertRaises(ConvertibleClassValidationError):
            SignEConsentRequestObject.from_dict(request_sample)

    def test_failure_create_no_signature_field(self):
        request_sample = simple_econsent_log()
        request_sample.pop("signature", None)
        with self.assertRaises(ConvertibleClassValidationError):
            SignEConsentRequestObject.from_dict(request_sample)

    def test_failure_create_no_user_id_field(self):
        request_sample = simple_econsent_log()
        request_sample.pop("userId", None)
        with self.assertRaises(ConvertibleClassValidationError):
            SignEConsentRequestObject.from_dict(request_sample)

    def test_failure_create_no_econsent_id_field(self):
        request_sample = simple_econsent_log()
        request_sample.pop("econsentId", None)
        with self.assertRaises(ConvertibleClassValidationError):
            SignEConsentRequestObject.from_dict(request_sample)

    @patch("extensions.deployment.tasks.update_econsent_pdf_location.delay")
    def test_success_check_upload_econsent_pdf(self, mock_func):
        celery_app.conf.task_always_eager = True
        use_case = SignEConsentUseCase(ec_repo=MockEConsentRepo(), dep_repo=MagicMock())
        use_case.execute(self.request_object)
        mock_func.assert_called_once()

    @patch("extensions.deployment.tasks.update_econsent_pdf_location.delay")
    def test_success_translate_econsent_pdf(self, mock_func):
        use_case = SignEConsentUseCase(ec_repo=MockEConsentRepo(), dep_repo=MagicMock())
        use_case.execute(self.request_object)
        mock_func.assert_called_once()
        arguments = mock_func.call_args.kwargs
        trans = get_translations()
        self.assertEqual(trans[TITLE_TRANSLATE], arguments["econsent"]["title"])
        self.assertEqual(
            trans[ADDITIONAL_QUESTION_TRANSLATE_PREFIX.format("1")],
            arguments["answers"][0]["question"],
        )
        self.assertEqual(
            trans[ADDITIONAL_QUESTION_TRANSLATE_PREFIX.format("2")],
            arguments["answers"][1]["question"],
        )
        self.assertEqual(trans[YES_TRANSLATE], arguments["other_strings"]["yes"])
        self.assertEqual(trans[NO_TRANSLATE], arguments["other_strings"]["no"])


class EconsentCreationTestCase(TestCase):
    def test_success_strip_urls_econsent(self):
        econsent_dict = simple_econsent()
        url = "    https://some.url/     "
        econsent_dict[EConsent.SECTIONS][1][EConsentSection.THUMBNAIL_URL] = url
        econsent_dict[EConsent.SECTIONS][1][EConsentSection.VIDEO_URL] = url
        econsent = EConsent.from_dict(econsent_dict)
        self.assertEqual(econsent.sections[1].thumbnailUrl, url.strip())
        self.assertEqual(econsent.sections[1].videoUrl, url.strip())
