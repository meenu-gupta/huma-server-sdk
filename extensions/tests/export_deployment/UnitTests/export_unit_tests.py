import copy
import unittest
from collections import defaultdict
from datetime import datetime
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from extensions.authorization.models.user import User
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.export_deployment.helpers.convertion_helpers import (
    filter_not_included_fields,
    DEFAULT_INCLUDED_FIELDS,
    deidentify_dict,
    generate_user_metadata,
    attach_users_data,
    exclude_fields,
    flatten_data,
    retrieve_users_data,
    get_consents_meta_data,
    get_consent_data,
    get_econsent_data,
    build_module_config_versions,
    replace_answer_text_with_short_codes,
)
from extensions.export_deployment.helpers.translation_helpers import translate_object
from extensions.export_deployment.models.export_deployment_models import (
    DEFAULT_DEIDENTIFY_REMOVE_FIELDS,
    DEFAULT_DEIDENTIFY_HASH_FIELDS,
    DEFAULT_EXCLUDE_FIELDS,
    ExportProcess,
    ExportResultObject,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.repository.mongo_export_deployment_repository import (
    MongoExportDeploymentRepository,
)
from extensions.export_deployment.tasks import (
    clean_user_export_results,
    mark_stuck_export_processes_as_failed,
    mark_process_failed,
)
from extensions.export_deployment.use_case.export_request_objects import (
    ExportRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    ExportDeploymentUseCase,
)
from extensions.export_deployment.use_case.exportable.exportable_request_objects import (
    ExportableRequestObject,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.medication.models.medication import Medication
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import Primitive, QuestionnaireAnswer
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.tests.export_deployment.IntegrationTests.user_export_tests import (
    EXISTING_TASK_ID,
)
from extensions.tests.export_deployment.UnitTests.export_deployment_use_case_tests import (
    get_export_repo,
    LATEST_CONSENT_ID,
    get_deployment_repo,
    SAMPLE_DEPLOYMENT_ID,
    LATEST_ECONSENT_ID,
    DEPLOYMENT_CODE,
    CONSENT_LOG,
    ECONSENT_LOG,
    MANAGER_ID,
)
from extensions.tests.export_deployment.UnitTests.policies_tests import DEPLOYMENT_ID
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.localization.utils import Localization, Language
from sdk.common.utils import inject
from sdk.common.utils.inject import Binder

ENROLLMENT_ID = 100
MODULE_NAME = "Module"
MODULE_CONFIG_ID = "5e8f0c74b50aa9656c34789a"
CONFIG_BODY_ID = "sample_cfg"
TEST_VERSION = 1
USER_FIELD = "user"
PRIMITIVE_ID = "5e8f0c74b50aa9656c34789b"
USER_ID = "5fe0b3bb2896c6d525461087"
CONSENT_ID = "5e8f0c74b50aa9656c34789d"
ECONSENT_ID = "5e8f0c74b50aa9656c34789e"
USER_DATA_SAMPLE = {
    User.PRIMARY_ADDRESS: "home",
    User.GIVEN_NAME: "Test",
    User.FAMILY_NAME: "Tester",
    User.EMAIL: "email@huma.com",
    User.PHONE_NUMBER: "+440101233022",
    User.ADDITIONAL_CONTACT_DETAILS: 0,
    User.PERSONAL_DOCUMENTS: 0,
    User.FAMILY_MEDICAL_HISTORY: 0,
    User.EXTRA_CUSTOM_FIELDS: 0,
    User.NHS: 0,
    User.WECHAT_ID: 0,
    User.KARDIA_ID: 0,
    User.INSURANCE_NUMBER: 0,
    User.PAM_THIRD_PARTY_IDENTIFIER: 0,
    User.EMERGENCY_PHONE_NUMBER: 0,
    User.ID: USER_ID,
}

PRIMITIVE_SAMPLE = {
    Primitive.ID: PRIMITIVE_ID,
    Primitive.CREATE_DATE_TIME: datetime.utcnow(),
    Primitive.USER_ID: USER_ID,
    Primitive.SUBMITTER_ID: USER_ID,
}
PRIMITIVE_SAMPLE_WITH_USER = {
    **PRIMITIVE_SAMPLE,
    USER_FIELD: USER_DATA_SAMPLE,
}


CONSENTS_DATA = {USER_ID: Consent(id=CONSENT_ID)}
ECONSENTS_DATA = {USER_ID: EConsent(id=ECONSENT_ID)}

TEST_KEY = f"user/{USER_ID}/exports/{EXISTING_TASK_ID}/export.zip"
TEST_BUCKET = "test"


def get_export_data(include_user=True):
    if include_user:
        sample = copy.deepcopy(PRIMITIVE_SAMPLE_WITH_USER)
    else:
        sample = copy.deepcopy(PRIMITIVE_SAMPLE)
    return {MODULE_NAME: [sample]}


def deidentify(data: dict, deidentify=True):
    deidentify_dict(
        data,
        deidentify_exclude_fields=DEFAULT_DEIDENTIFY_REMOVE_FIELDS,
        deidentify_hash_fields=DEFAULT_DEIDENTIFY_HASH_FIELDS,
        deidentify=deidentify,
        fields_to_exclude=DEFAULT_EXCLUDE_FIELDS,
    )


DEFAULT_KEY = "default_key"
DEFAULT_TRANSLATION = "DEFAULT"


class ExportTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind_and_configure(binder):
            localization = MagicMock()
            localization.get.return_value = {
                Language.EN: {DEFAULT_KEY: DEFAULT_TRANSLATION}
            }
            binder.bind(Localization, localization)

        inject.clear_and_configure(bind_and_configure)

    def test_get_modules_adds_subclasses(self):
        # to initiate modules so they were available in __subclasses__()
        default_modules = ModulesManager().default_modules
        modules = ExportableUseCase.get_modules(None, None)
        modules = [m.__class__ for m in modules]
        for module in Module.__subclasses__():
            self.assertIn(module, modules)
            for module_subclass in module.__subclasses__():
                self.assertIn(module_subclass, modules)
        for default_module in default_modules:
            self.assertIn(default_module.__class__, modules)

    def test_create_date_field_in_primitives_query(self):
        start_date = end_date = datetime.utcnow()
        create_date_class = Medication
        create_field_query = MongoExportDeploymentRepository._get_query_date_range(
            start_date, end_date, False, create_date_class
        )
        self.assertIn(Primitive.CREATE_DATE_TIME, create_field_query)
        self.assertNotIn(Primitive.START_DATE_TIME, create_field_query)

        create_field_partly_query = (
            MongoExportDeploymentRepository._get_query_date_range(
                start_date, end_date, True, create_date_class
            )
        )
        or_query_part = create_field_partly_query["$or"]
        self.assertEqual(len(or_query_part), 2)
        start_query_part = or_query_part[0]
        self.assertIn(Primitive.CREATE_DATE_TIME, start_query_part)
        self.assertNotIn(Primitive.START_DATE_TIME, start_query_part)

    def test_create_date_field_in_primitives_query_on_use_creation_time(self):
        start_date = end_date = datetime.utcnow()
        create_date_class = Medication
        create_field_query = MongoExportDeploymentRepository._get_query_date_range(
            start_date, end_date, False, create_date_class, use_creation_time=True
        )
        self.assertIn(Primitive.CREATE_DATE_TIME, create_field_query)
        self.assertNotIn(Primitive.START_DATE_TIME, create_field_query)

        create_field_partly_query = (
            MongoExportDeploymentRepository._get_query_date_range(
                start_date, end_date, True, create_date_class, use_creation_time=True
            )
        )
        or_query_part = create_field_partly_query["$or"]
        self.assertEqual(len(or_query_part), 2)
        start_query_part = or_query_part[0]
        self.assertIn(Primitive.CREATE_DATE_TIME, start_query_part)
        self.assertNotIn(Primitive.START_DATE_TIME, start_query_part)

    def test_start_date_field_in_primitives_query(self):
        start_date = end_date = datetime.utcnow()
        start_date_class = Primitive
        start_field_query = MongoExportDeploymentRepository._get_query_date_range(
            start_date, end_date, False, start_date_class
        )
        self.assertIn(Primitive.START_DATE_TIME, start_field_query)
        self.assertNotIn(Primitive.CREATE_DATE_TIME, start_field_query)

        start_field_partly_query = (
            MongoExportDeploymentRepository._get_query_date_range(
                start_date, end_date, True, start_date_class
            )
        )
        or_query_part = start_field_partly_query["$or"]
        self.assertEqual(len(or_query_part), 2)
        start_query_part = or_query_part[0]
        self.assertIn(Primitive.START_DATE_TIME, start_query_part)
        self.assertNotIn(Primitive.CREATE_DATE_TIME, start_query_part)

    def test_replace_localizable_keys(self):
        module_name = "Symptom"
        primitive_key_one = "primitive key 1"
        primitive_value_one = "huma localizable key one"
        english_value = "english value"
        arabic_value = "arabic value"
        spanish_value = "spanish value"

        raw_module_result = {
            module_name: [
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "ar"},
                },
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "es"},
                },
            ]
        }
        deployment = Deployment()
        deployment.localizations = {
            "en": {primitive_value_one: english_value},
            "ar": {primitive_value_one: arabic_value},
            "es": {primitive_value_one: spanish_value},
        }
        request_object = ExportableRequestObject()
        request_object.doTranslate = True
        ExportableUseCase.replace_localizable_keys_if_requested(
            request_object, raw_module_result, deployment
        )
        self.assertEqual(
            raw_module_result[module_name][0][primitive_key_one], arabic_value
        )
        self.assertEqual(
            raw_module_result[module_name][1][primitive_key_one], spanish_value
        )

    def test_replace_localizable_keys_with_default_localization(self):
        module_name = "Symptom"

        raw_module_result = {
            module_name: [
                {
                    DEFAULT_KEY: DEFAULT_TRANSLATION,
                    USER_FIELD: {User.LANGUAGE: Language.EN},
                },
            ]
        }
        deployment = Deployment()
        deployment.localizations = None
        request_object = ExportableRequestObject()
        request_object.doTranslate = True
        ExportableUseCase.replace_localizable_keys_if_requested(
            request_object, raw_module_result, deployment
        )
        self.assertEqual(
            DEFAULT_TRANSLATION, raw_module_result[module_name][0][DEFAULT_KEY]
        )

    def test_replace_localizable_keys_with_no_localization(self):
        module_name = "Symptom"
        primitive_key_one = "primitive key 1"
        primitive_value_one = "huma localizable key one"

        raw_module_result = {
            module_name: [
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "ar"},
                },
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "es"},
                },
            ]
        }
        deployment = Deployment()
        request_object = ExportableRequestObject()
        request_object.doTranslate = True
        ExportableUseCase.replace_localizable_keys_if_requested(
            request_object, raw_module_result, deployment
        )
        self.assertEqual(
            raw_module_result[module_name][0][primitive_key_one], primitive_value_one
        )
        self.assertEqual(
            raw_module_result[module_name][1][primitive_key_one], primitive_value_one
        )

    def test_replace_localizable_keys_with_unknown_user_language_fallback_to_en(self):
        module_name = "Symptom"
        primitive_key_one = "primitive key 1"
        primitive_value_one = "huma localizable key one"
        english_value = "english value"

        raw_module_result = {
            module_name: [
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "ar"},
                },
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "es"},
                },
            ]
        }
        deployment = Deployment()
        deployment.localizations = {
            "en": {primitive_value_one: english_value},
        }
        request_object = ExportableRequestObject()
        request_object.doTranslate = True
        ExportableUseCase.replace_localizable_keys_if_requested(
            request_object, raw_module_result, deployment
        )
        self.assertEqual(
            raw_module_result[module_name][0][primitive_key_one], english_value
        )
        self.assertEqual(
            raw_module_result[module_name][1][primitive_key_one], english_value
        )

    def test_replace_localizable_keys_comma_separated(self):
        module_name = "Symptom"
        primitive_key_one = "primitive key 1"
        primitive_value_one = "huma localizable key one"
        english_value = "english value"
        arabic_value = "arabic value"
        spanish_value = "spanish value"

        comma_separated_primitive_value = ",".join([primitive_value_one] * 3)
        comma_separated_spanish_value = ",".join([spanish_value] * 3)

        raw_module_result = {
            module_name: [
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "ar"},
                },
                {
                    primitive_key_one: primitive_value_one,
                    USER_FIELD: {User.LANGUAGE: "es"},
                },
                {
                    primitive_key_one: comma_separated_primitive_value,
                    USER_FIELD: {User.LANGUAGE: "es"},
                },
            ]
        }
        deployment = Deployment()
        deployment.localizations = {
            "en": {primitive_value_one: english_value},
            "ar": {primitive_value_one: arabic_value},
            "es": {primitive_value_one: spanish_value},
        }
        request_object = ExportableRequestObject()
        request_object.doTranslate = True
        ExportableUseCase.replace_localizable_keys_if_requested(
            request_object, raw_module_result, deployment
        )
        self.assertEqual(
            raw_module_result[module_name][2][primitive_key_one],
            comma_separated_spanish_value,
        )

    def test_translate_object(self):
        translated_value = "TRANSLATED"
        value_to_translate = "to_translate"
        translatable_value = f" {value_to_translate} "
        not_translatable = f"{value_to_translate} test"
        translation_short_codes = {value_to_translate: translated_value}

        object_to_translate = {
            "listField": ["some", value_to_translate],
            translatable_value: 15,
            not_translatable: 10,
        }
        expected_translated_object = {
            "listField": ["some", translated_value],
            translated_value: 15,
            not_translatable: 10,
        }

        result = translate_object(object_to_translate, translation_short_codes)
        self.assertEqual(expected_translated_object, result)

    def test_filter_not_included_fields_keeps_default_fields(self):
        include_fields = [Primitive.SERVER, Primitive.SUBMITTER_ID]

        test_primitive_dict = {
            Primitive.USER_ID: "userId",
            Primitive.MODULE_ID: "module",
            Primitive.CREATE_DATE_TIME: "time",
            Primitive.DEPLOYMENT_ID: "deployment",
            Primitive.SERVER: "server",
            Primitive.SUBMITTER_ID: "submitter",
        }
        filter_not_included_fields(include_fields, test_primitive_dict)
        for field in DEFAULT_INCLUDED_FIELDS:
            self.assertIn(field, test_primitive_dict)
        for field in include_fields:
            self.assertIn(field, test_primitive_dict)
        self.assertNotIn(Primitive.DEPLOYMENT_ID, test_primitive_dict)

    def test_deidentify_dict__nulls_proper_fields(self):
        sample = copy.deepcopy(PRIMITIVE_SAMPLE_WITH_USER)
        sample["listField"] = [{Primitive.USER_ID: USER_ID}, "something"]
        deidentify(sample)
        for field in DEFAULT_DEIDENTIFY_REMOVE_FIELDS:
            primitive_field = sample.get(field)
            user_field = sample[USER_FIELD].get(field)
            self.assertIsNone(primitive_field)
            self.assertIsNone(user_field)
        self.assertNotEqual(sample["listField"][0][Primitive.USER_ID], USER_ID)

    def test_deidentify_dict__hashes_proper_fields(self):
        sample = copy.deepcopy(PRIMITIVE_SAMPLE_WITH_USER)
        deidentify(sample)
        for field in DEFAULT_DEIDENTIFY_HASH_FIELDS:
            self.assertIn(field, sample)
            self.assertNotEqual(sample[field], PRIMITIVE_SAMPLE_WITH_USER[field])
        for user_field in sample[USER_FIELD]:
            if user_field not in DEFAULT_DEIDENTIFY_HASH_FIELDS:
                continue
            self.assertNotEqual(
                sample[USER_FIELD][user_field],
                PRIMITIVE_SAMPLE_WITH_USER[USER_FIELD][user_field],
            )

    def test_deidentify_dict__skipped_when_deidentify_false(self):
        sample = copy.deepcopy(PRIMITIVE_SAMPLE_WITH_USER)
        deidentify(sample, False)
        self.assertEqual(sample, PRIMITIVE_SAMPLE_WITH_USER)

    def test_generate_user_metadata_with_null_fields(self):
        user = User(id=USER_ID, enrollmentNumber=ENROLLMENT_ID)
        deployment = Deployment(code=DEPLOYMENT_CODE, id=DEPLOYMENT_ID)
        data = generate_user_metadata(
            user, deployment, CONSENTS_DATA, {}, include_null_fields=True
        )
        self.assertIn(User.LANGUAGE, data)
        self.assertIsNone(data[User.LANGUAGE])

    def test_generate_user_metadata_without_null_fields(self):
        user = User(id=USER_ID, enrollmentNumber=ENROLLMENT_ID)
        deployment = Deployment(code=DEPLOYMENT_CODE, id=DEPLOYMENT_ID)
        data = generate_user_metadata(
            user, deployment, CONSENTS_DATA, {}, include_null_fields=False
        )
        self.assertNotIn(User.LANGUAGE, data)

    def test_generate_user_metadata(self):
        user = User(id=USER_ID, enrollmentNumber=ENROLLMENT_ID)
        deployment = Deployment(code=DEPLOYMENT_CODE, id=DEPLOYMENT_ID)
        data = generate_user_metadata(
            user, deployment, CONSENTS_DATA, ECONSENTS_DATA, include_null_fields=False
        )
        expected_meta = {
            **user.to_dict(include_none=False),
            "consent": {Consent.ID: CONSENT_ID, Consent.REVISION: 1},
            "econsent": {EConsent.ID: ECONSENT_ID, EConsent.REVISION: 1},
        }
        self.assertEqual(expected_meta, data)

    def test_attach_users_data(self):
        data = get_export_data(include_user=False)
        users_data = {USER_ID: USER_DATA_SAMPLE}
        attach_users_data(data, users_data)
        self.assertEqual(USER_DATA_SAMPLE, data[MODULE_NAME][0][USER_FIELD])

    def test_exclude_fields(self):
        data = get_export_data()
        fields_to_exclude = [f"{USER_FIELD}.{User.EMAIL}", Primitive.ID]
        exclude_fields(data, fields_to_exclude)
        self.assertNotIn(Primitive.ID, data[MODULE_NAME][0])
        self.assertNotIn(User.EMAIL, data[MODULE_NAME][0][USER_FIELD])

    def test_flatten_data(self):
        data = get_export_data()
        flatten_data(data)
        self.assertNotIn(USER_FIELD, data[MODULE_NAME][0])
        self.assertIn(f"{USER_FIELD}.{User.EMAIL}", data[MODULE_NAME][0])

    @patch(
        "extensions.export_deployment.helpers.convertion_helpers.generate_user_metadata"
    )
    def test_retrieve_users_data(self, mocked_generate):
        user = User(id=USER_ID, enrollmentNumber=ENROLLMENT_ID)
        deployment = Deployment(code=DEPLOYMENT_CODE, id=DEPLOYMENT_ID)
        data = get_export_data(include_user=False)
        users_data = {}
        export_repo_mock = MagicMock()
        export_repo_mock.retrieve_users.return_value = [user]
        retrieve_users_data(
            data,
            users_data,
            deployment,
            CONSENTS_DATA,
            ECONSENTS_DATA,
            False,
            export_repo_mock,
        )
        mocked_generate.assert_called_once_with(
            user, deployment, CONSENTS_DATA, ECONSENTS_DATA, False
        )
        self.assertIn(USER_ID, users_data)

    def test_get_consents_metadata(self):
        export_repo_mock = get_export_repo()
        consent = Consent(id=LATEST_CONSENT_ID)
        econsent = EConsent(id=LATEST_ECONSENT_ID)
        mocked_deployment_repo = get_deployment_repo(consent, econsent)
        consent_meta, econsent_meta = get_consents_meta_data(
            SAMPLE_DEPLOYMENT_ID, export_repo_mock, mocked_deployment_repo
        )
        self.assertEqual(consent_meta[USER_ID], CONSENT_LOG)
        self.assertEqual(econsent_meta[USER_ID], ECONSENT_LOG)

    def test_get_consent_data(self):
        consent = Consent(id=LATEST_CONSENT_ID)
        deployment = Deployment(id=DEPLOYMENT_ID, consent=consent)
        data = get_consent_data(deployment, get_export_repo())
        self.assertEqual({USER_ID: CONSENT_LOG}, data)

    def test_get_econsent_data(self):
        econsent = EConsent(id=LATEST_ECONSENT_ID)
        deployment = Deployment(id=DEPLOYMENT_ID, econsent=econsent)
        data = get_econsent_data(deployment, get_export_repo())
        self.assertEqual({USER_ID: ECONSENT_LOG}, data)

    def test_build_module_config_versions(self):
        versions = defaultdict(lambda: defaultdict(dict))
        config = ModuleConfig(
            id=MODULE_CONFIG_ID, moduleId=MODULE_NAME, version=TEST_VERSION
        )
        build_module_config_versions(versions, [config])
        self.assertEqual(config, versions[MODULE_NAME][MODULE_CONFIG_ID][TEST_VERSION])
        self.assertEqual(1, len(versions[MODULE_NAME]))

    def test_build_module_config_versions__with_questionnaire_id(self):
        versions = defaultdict(lambda: defaultdict(dict))
        config_body = {"id": CONFIG_BODY_ID}
        config = ModuleConfig(
            id=MODULE_CONFIG_ID,
            moduleId=MODULE_NAME,
            version=TEST_VERSION,
            configBody=config_body,
        )
        build_module_config_versions(versions, [config])
        self.assertEqual(config, versions[MODULE_NAME][MODULE_CONFIG_ID][TEST_VERSION])
        self.assertEqual(config, versions[MODULE_NAME][CONFIG_BODY_ID][TEST_VERSION])
        self.assertEqual(2, len(versions[MODULE_NAME]))

    def test_replace_answer_text_with_short_codes(self):
        short_code = "short_code"
        question_id = "9f0c0b00-8541-4a0a-a8ba-c8eb4a629af7"
        answer_data = {
            QuestionnaireAnswer.ANSWER_TEXT: "Bad",
            QuestionnaireAnswer.QUESTION_ID: question_id,
            QuestionnaireAnswer.QUESTION: "some_text",
        }
        module_config = ModuleConfig(
            configBody={
                "name": "Some",
                "id": "6d4ea71a-7554-4315-8e67-53bfbc0760b1",
                "pages": [
                    {
                        "type": "QUESTION",
                        "items": [
                            {
                                "id": question_id,
                                "format": "TEXTCHOICE",
                                "exportShortCode": short_code,
                                "text": "some_text",
                                "options": [
                                    {"label": "Ok", "value": "0", "weight": 0},
                                    {"label": "Bad", "value": "1", "weight": 1},
                                ],
                                "selectionCriteria": "SINGLE",
                            }
                        ],
                    }
                ],
            }
        )
        replace_answer_text_with_short_codes([answer_data], module_config)
        self.assertEqual(short_code, answer_data[QuestionnaireAnswer.QUESTION])

    def test_retrieve_users(self):
        mocked_auth_repo = MagicMock()
        mocked_users = [USER_ID]
        mocked_auth_repo.retrieve_user_ids_with_assigned_manager.side_effect = [
            [],
            mocked_users,
        ]

        use_case = ExportDeploymentUseCase(
            export_repo=MagicMock(),
            deployment_repo=MagicMock(),
            file_storage=MagicMock(),
            organization_repo=MagicMock(),
            auth_repo=mocked_auth_repo,
        )
        use_case.request_object = ExportRequestObject(
            deploymentId=DEPLOYMENT_ID, managerId=MANAGER_ID
        )

        users = use_case.retrieve_users()
        self.assertEqual([], users)

        users = use_case.retrieve_users()
        self.assertEqual(mocked_users, users)


class ExportTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = MagicMock()
        self.repo = MagicMock()
        self.existing_process = ExportProcess(
            resultObject=ExportResultObject(key=TEST_KEY, bucket=TEST_BUCKET),
            id=EXISTING_TASK_ID,
            status=ExportProcess.ExportStatus.DONE,
        )
        self.repo.retrieve_export_processes.return_value = [self.existing_process]

        def configure_with_binder(binder: Binder):
            binder.bind(ExportDeploymentRepository, self.repo)
            binder.bind(FileStorageAdapter, self.adapter)

        inject.clear_and_configure(config=configure_with_binder)

    def test_clean_user_export_results(self):
        time = datetime.utcnow()
        with freeze_time(time):
            clean_user_export_results()
        self.repo.retrieve_export_processes.assert_called_once_with(
            export_type=[
                ExportProcess.ExportType.USER,
                ExportProcess.ExportType.SUMMARY_REPORT,
            ],
            status=ExportProcess.ExportStatus.DONE,
            till_date=time - relativedelta(days=7),
        )
        expected_delete_key = f"user/{USER_ID}/exports/{EXISTING_TASK_ID}"
        self.adapter.delete_folder.assert_called_once_with(
            self.existing_process.resultObject.bucket, expected_delete_key
        )
        self.repo.delete_export_process.assert_called_once_with(EXISTING_TASK_ID)

    @patch("extensions.export_deployment.tasks.mark_process_failed")
    def test_mark_stuck_export_processes_as_failed(self, mocked_mark_failed):
        time = datetime.utcnow()
        with freeze_time(time):
            mark_stuck_export_processes_as_failed()
        self.repo.retrieve_export_processes.assert_called_once_with(
            status=ExportProcess.ExportStatus.PROCESSING,
            till_date=time - relativedelta(hours=2),
        )
        mocked_mark_failed.assert_called_once_with(EXISTING_TASK_ID)

    def test_mark_process_failed(self):
        mark_process_failed(EXISTING_TASK_ID)
        self.repo.update_export_process.assert_called_once_with(
            EXISTING_TASK_ID,
            ExportProcess(
                status=ExportProcess.ExportStatus.ERROR,
                seen=False,
            ),
        )

    def test_export_process_has_no_default(self):
        process = ExportProcess()
        self.assertIsNone(process.status)
        self.assertIsNone(process.exportType)
        self.assertIsNone(process.seen)
