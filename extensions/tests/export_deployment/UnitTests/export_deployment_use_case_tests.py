from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.authorization.models.user import User
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.deployment.models.consent.consent import Consent
from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.repository.deployment_repository import DeploymentRepository
from extensions.export_deployment.models.export_deployment_models import (
    ExportProfile,
    ExportParameters,
    ExportProcess,
)
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from extensions.export_deployment.use_case.export_request_objects import (
    RetrieveExportDeploymentProcessesRequestObject,
    CheckExportDeploymentTaskStatusRequestObject,
    RunExportTaskRequestObject,
    ExportRequestObject,
    RetrieveUserExportProcessesRequestObject,
    RunAsyncUserExportRequestObject,
)
from extensions.export_deployment.use_case.export_use_cases import (
    RetrieveExportDeploymentProcessesUseCase,
    CheckExportTaskStatusUseCase,
    RunExportTaskUseCase,
    ExportDeploymentUseCase,
    RetrieveUserExportProcessesUseCase,
    AsyncExportUserDataUseCase,
)
from extensions.export_deployment.use_case.exportable.module_exportable_use_case import (
    ModuleExportableUseCase,
)
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.modules.modules_manager import ModulesManager
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.exceptions.exceptions import InvalidRequestException, ObjectDoesNotExist
from sdk.common.localization.utils import Localization
from sdk.common.utils import inject
from sdk.versioning.models.version import Version

SAMPLE_DEPLOYMENT_ID = "5fe0b3bb2896c6d525461086"
USE_CASES_PATH = "extensions.export_deployment.use_case.export_use_cases"
SIGNED_USER_ID = "5fe0b3bb2896c6d525461087"
MANAGER_ID = "5fe0b3bb2896c6d525461082"
NOT_SIGNED_USER_ID = "5fe0b3bb2896c6d525461088"
NOT_SIGNED_LATEST_USER_ID = "5fe0b3bb2896c6d525461089"
LATEST_CONSENT_LOG = "5fe0b3bb2896c6d525461090"
LATEST_CONSENT_ID = "5fe0b3bb2896c6d525461092"
LATEST_ECONSENT_LOG = "5fe0b3bb2896c6d525461080"
LATEST_ECONSENT_ID = "5fe0b3bb2896c6d525461082"
CONSENT_LOG = ConsentLog(
    id=LATEST_CONSENT_LOG, userId=SIGNED_USER_ID, consentId=LATEST_CONSENT_ID
)
ECONSENT_LOG = EConsentLog(
    id=LATEST_ECONSENT_LOG, userId=SIGNED_USER_ID, econsentId=LATEST_ECONSENT_ID
)
MODULE_ID = "Some"
DEPLOYMENT_CODE = "DE"


def get_sample_raw_module_data(_):
    return {
        MODULE_ID: [
            {
                Primitive.ID: "123",
                Primitive.USER_ID: SIGNED_USER_ID,
                Primitive.MODULE_ID: MODULE_ID,
            },
            {
                Primitive.ID: "124",
                Primitive.USER_ID: NOT_SIGNED_USER_ID,
                Primitive.MODULE_ID: MODULE_ID,
            },
        ]
    }


class TestRetrieveExportProcessesUseCase(TestCase):
    def test_success_retrieve_deployment_export_processes(self):
        request_object = RetrieveExportDeploymentProcessesRequestObject.from_dict(
            {"deploymentId": SAMPLE_DEPLOYMENT_ID}
        )
        mocked_export_repo = MagicMock()
        RetrieveExportDeploymentProcessesUseCase(repo=mocked_export_repo).execute(
            request_object
        )
        mocked_export_repo.retrieve_export_processes.assert_called_with(
            deployment_id=SAMPLE_DEPLOYMENT_ID,
            export_type=[ExportProcess.ExportType.DEFAULT],
        )

    def test_success_retrieve_user_export_processes(self):
        request_object = RetrieveUserExportProcessesRequestObject.from_dict(
            {RetrieveUserExportProcessesRequestObject.USER_ID: SIGNED_USER_ID}
        )
        mocked_export_repo = MagicMock()
        RetrieveUserExportProcessesUseCase(repo=mocked_export_repo).execute(
            request_object
        )
        mocked_export_repo.retrieve_export_processes.assert_called_with(
            user_id=SIGNED_USER_ID,
            export_type=[
                ExportProcess.ExportType.USER,
                ExportProcess.ExportType.SUMMARY_REPORT,
            ],
        )


class TestCheckExportDeploymentTaskStatusUseCase(TestCase):
    def test_success_check_export_deployment_task(self):
        request_object = CheckExportDeploymentTaskStatusRequestObject.from_dict(
            {
                "exportProcessId": "5fe0b52b24f10259fa13bf1b",
                "deploymentId": SAMPLE_DEPLOYMENT_ID,
            }
        )
        mocked_export_repo = MagicMock()
        CheckExportTaskStatusUseCase(repo=mocked_export_repo).execute(request_object)
        mocked_export_repo.retrieve_export_process.assert_called_with(
            "5fe0b52b24f10259fa13bf1b"
        )


class TestRunExportDeploymentTaskUseCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mocked_export_repo = MagicMock()

        def bind(binder):
            binder.bind(ExportDeploymentRepository, cls.mocked_export_repo)

        inject.clear_and_configure(bind)

    @patch(f"{USE_CASES_PATH}.run_export", MagicMock())
    def test_success_run_export_deployment_task(self):
        request_object = RunExportTaskRequestObject.from_dict(
            {
                RunExportTaskRequestObject.REQUESTER_ID: MANAGER_ID,
                RunExportTaskRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            }
        )
        repo = MagicMock()
        repo.check_export_process_already_running_for_user.return_value = False
        RunExportTaskUseCase(repo=repo).execute(request_object)
        repo.create_export_process.assert_called_once()
        export_obj = repo.create_export_process.call_args_list[0].args[0]
        self.assertEqual(ExportProcess.ExportType.DEFAULT, export_obj.exportType)
        self.assertEqual(ExportProcess.ExportStatus.CREATED, export_obj.status)
        self.assertTrue(export_obj.seen)

    @patch(f"{USE_CASES_PATH}.extract_user", MagicMock())
    @patch(f"{USE_CASES_PATH}.AuthorizedUser")
    @patch.object(RunExportTaskUseCase, "execute")
    def test_success_run_user_export_async_usecase(
        self, mocked_export_use_case_execute, mocked_authz_user
    ):
        mocked_authz_user().deployment_ids.return_value = [SAMPLE_DEPLOYMENT_ID]
        request_object = RunAsyncUserExportRequestObject.from_dict(
            {
                RunAsyncUserExportRequestObject.REQUESTER_ID: MANAGER_ID,
                RunAsyncUserExportRequestObject.USER_ID: SIGNED_USER_ID,
            }
        )
        AsyncExportUserDataUseCase().execute(request_object)
        request_obj = mocked_export_use_case_execute.call_args_list[0].args[0]
        self.assertEqual(ExportProcess.ExportType.USER, request_obj.exportType)

    def test_failure_export_process_is_already_running(self):
        request_object = RunExportTaskRequestObject.from_dict(
            {
                RunExportTaskRequestObject.REQUESTER_ID: MANAGER_ID,
                RunExportTaskRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            }
        )
        repo = MagicMock()
        repo.check_export_process_already_running_for_user.return_value = True
        with self.assertRaises(InvalidRequestException):
            RunExportTaskUseCase(repo=repo).execute(request_object)


class TestExportDeploymentUseCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mocked_version = Version(server="1.11.0")
        cls.mocked_export_repo = get_export_repo()

        def bind(binder):
            deployment_repo = MagicMock()
            deployment_repo.retrieve_deployment.return_value = Deployment()
            binder.bind(DeploymentRepository, deployment_repo)
            binder.bind(ExportDeploymentRepository, cls.mocked_export_repo)
            binder.bind(OrganizationRepository, MagicMock())
            binder.bind(FileStorageAdapter, MagicMock())
            binder.bind(Version, cls.mocked_version)
            binder.bind(AuthorizationRepository, MagicMock())
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(bind)

    def test_success_export_deployment(self):
        # to initiate modules so they were available in __subclasses__()
        ModulesManager().default_modules
        request_object = ExportRequestObject.from_dict(
            {ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID}
        )
        ExportDeploymentUseCase().execute(request_object)
        self.mocked_export_repo.retrieve_primitives.assert_called()

    @patch(f"{USE_CASES_PATH}.ExportDeploymentUseCase.process_request")
    def test_success_export_deployment_with_export_profile(
        self, mocked_process_request
    ):
        profile_name = "test"
        profile_export_content = {
            ExportParameters.LAYER: ExportParameters.DataLayerOption.FLAT.value,
            ExportParameters.FROM_DATE: datetime.utcnow().date().isoformat(),
        }
        profile_data = {
            ExportProfile.NAME: profile_name,
            ExportProfile.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportProfile.CONTENT: profile_export_content,
        }
        export_profile = ExportProfile.from_dict(profile_data)
        request_object = ExportRequestObject.from_dict(
            {
                ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                ExportRequestObject.BASE_PROFILE: profile_name,
            }
        )

        merged_request_object = ExportRequestObject.from_dict(
            {
                **profile_export_content,
                **request_object.to_dict(include_none=False),
            }
        )
        mocked_export_repo = MagicMock()
        mocked_export_repo.retrieve_export_profile.return_value = export_profile

        use_case = ExportDeploymentUseCase(
            export_repo=mocked_export_repo,
            deployment_repo=MagicMock(),
            file_storage=MagicMock(),
            organization_repo=MagicMock(),
        )
        use_case.execute(request_object)
        self.assertNotEqual(merged_request_object, request_object)
        mocked_process_request.assert_called_with(merged_request_object)

    @patch(f"{USE_CASES_PATH}.ExportDeploymentUseCase.process_request")
    def test_export_deployment_with_manager_id(self, _):
        request_object = ExportRequestObject.from_dict(
            {
                ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
                ExportRequestObject.MANAGER_ID: MANAGER_ID,
                ExportRequestObject.USE_EXPORT_PROFILE: False,
            }
        )
        auth_repo = MagicMock()
        use_case = ExportDeploymentUseCase(
            export_repo=MagicMock(),
            deployment_repo=MagicMock(),
            file_storage=MagicMock(),
            organization_repo=MagicMock(),
            auth_repo=auth_repo,
        )
        use_case.execute(request_object)
        auth_repo.retrieve_user_ids_with_assigned_manager.assert_called_once_with(
            MANAGER_ID
        )

    @patch(f"{USE_CASES_PATH}.get_default_export_profile")
    @patch(f"{USE_CASES_PATH}.ExportDeploymentUseCase.process_request")
    def test_success_export_deployment_uses_default_profile_if_any(
        self, mocked_process_request, mocked_get_default_profile
    ):
        test_from = (datetime.utcnow() + timedelta(days=500)).date()
        profile_name = "test"
        profile_export_content = {
            ExportParameters.LAYER: ExportParameters.DataLayerOption.FLAT.value,
            ExportParameters.FROM_DATE: test_from.isoformat(),
        }
        profile_data = {
            ExportProfile.NAME: profile_name,
            ExportProfile.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportProfile.CONTENT: profile_export_content,
        }
        export_profile = ExportProfile.from_dict(profile_data)
        request_object = ExportRequestObject.from_dict(
            {
                ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            }
        )

        mocked_export_repo = MagicMock()
        mocked_get_default_profile.return_value = export_profile
        use_case = ExportDeploymentUseCase(
            export_repo=mocked_export_repo,
            deployment_repo=MagicMock(),
            file_storage=MagicMock(),
            organization_repo=MagicMock(),
        )
        use_case.execute(request_object)
        mocked_get_default_profile.assert_called()
        export_call_request_object = mocked_process_request.call_args.args[0]
        self.assertEqual(export_call_request_object.fromDate.date(), test_from)

    @patch.object(ModuleExportableUseCase, "replace_localizable_keys_if_requested")
    @patch.object(ModuleExportableUseCase, "get_raw_result", get_sample_raw_module_data)
    def test_export_deployment__enrollment_number_present(self, mocked_localization):
        export_data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.INCLUDE_USER_META_DATA: True,
        }
        request_object = ExportRequestObject.from_dict(export_data)

        mocked_deployment_repo = get_deployment_repo()
        use_case = get_export_use_case(mocked_deployment_repo)
        use_case.execute(request_object)
        data = mocked_localization.call_args.args[1]
        # expected to have both data samples
        enrollment_number = data[MODULE_ID][0]["user"].get(User.ENROLLMENT_NUMBER)
        self.assertEqual("DE-0100", enrollment_number)

    @patch.object(ModuleExportableUseCase, "replace_localizable_keys_if_requested")
    @patch.object(ModuleExportableUseCase, "get_raw_result", get_sample_raw_module_data)
    def test_export_deployment_no_consent(self, mocked_localization):
        export_data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.INCLUDE_USER_META_DATA: True,
        }
        request_object = ExportRequestObject.from_dict(export_data)

        mocked_deployment_repo = get_deployment_repo()
        use_case = get_export_use_case(mocked_deployment_repo)
        use_case.execute(request_object)
        data = mocked_localization.call_args.args[1]
        # expected to have both data samples
        self.assertEqual(2, len(data[MODULE_ID]))

    @patch.object(ModuleExportableUseCase, "replace_localizable_keys_if_requested")
    @patch.object(ModuleExportableUseCase, "get_raw_result", get_sample_raw_module_data)
    def test_export_deployment_consent(self, mocked_localization):
        export_data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.INCLUDE_USER_META_DATA: True,
            ExportRequestObject.INCLUDE_NULL_FIELDS: False,
        }
        request_object = ExportRequestObject.from_dict(export_data)

        consent = Consent(id=LATEST_CONSENT_ID)
        mocked_deployment_repo = get_deployment_repo(consent)
        use_case = get_export_use_case(mocked_deployment_repo)
        use_case.execute(request_object)
        data = mocked_localization.call_args.args[1]
        # expected to have only 1 user as he's the only one who signed the latest consent
        self.assertEqual(1, len(data))
        user_data = data[MODULE_ID][0]
        self.assertIn("consent", user_data["user"])
        ignored_consent_fields = (
            ConsentLog.ID,
            ConsentLog.USER_ID,
            ConsentLog.CONSENT_ID,
        )
        consent_data = CONSENT_LOG.to_dict(
            include_none=False, ignored_fields=ignored_consent_fields
        )
        self.assertEqual(user_data["user"]["consent"], consent_data)

    @patch.object(ModuleExportableUseCase, "replace_localizable_keys_if_requested")
    @patch.object(ModuleExportableUseCase, "get_raw_result", get_sample_raw_module_data)
    def test_export_deployment_econsent(self, mocked_localization):
        export_data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.INCLUDE_USER_META_DATA: True,
            ExportRequestObject.INCLUDE_NULL_FIELDS: False,
        }
        request_object = ExportRequestObject.from_dict(export_data)

        econsent = EConsent(id=LATEST_ECONSENT_ID)
        mocked_deployment_repo = get_deployment_repo(econsent=econsent)
        use_case = get_export_use_case(mocked_deployment_repo)
        use_case.execute(request_object)
        data = mocked_localization.call_args.args[1]
        self.assertEqual(1, len(data))
        user_data = data[MODULE_ID][0]
        self.assertIn("econsent", user_data["user"])
        ignored_consent_fields = (
            EConsentLog.ID,
            EConsentLog.USER_ID,
            EConsentLog.ECONSENT_ID,
        )
        econsent_data = ECONSENT_LOG.to_dict(
            include_none=False, ignored_fields=ignored_consent_fields
        )
        self.assertEqual(user_data["user"]["econsent"], econsent_data)

    @patch.object(ModuleExportableUseCase, "replace_localizable_keys_if_requested")
    @patch.object(ModuleExportableUseCase, "get_raw_result", get_sample_raw_module_data)
    def test_export_deployment___enrollment_number_added(self, mocked_localization):
        export_data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.INCLUDE_USER_META_DATA: True,
            ExportRequestObject.INCLUDE_NULL_FIELDS: False,
        }
        request_object = ExportRequestObject.from_dict(export_data)

        consent = Consent(id=LATEST_CONSENT_ID)
        mocked_deployment_repo = get_deployment_repo(consent)
        use_case = get_export_use_case(mocked_deployment_repo)
        use_case.execute(request_object)
        data = mocked_localization.call_args.args[1]
        # expected to have only 1 user as he's the only one who signed the latest consent
        self.assertEqual(1, len(data))
        user_data = data[MODULE_ID][0]
        self.assertIn("consent", user_data["user"])
        ignored_consent_fields = (
            ConsentLog.ID,
            ConsentLog.USER_ID,
            ConsentLog.CONSENT_ID,
        )
        consent_data = CONSENT_LOG.to_dict(
            include_none=False, ignored_fields=ignored_consent_fields
        )
        self.assertEqual(user_data["user"]["consent"], consent_data)


def get_export_use_case(deployment_repo):
    mocked_export_repo = get_export_repo()
    use_case = ExportDeploymentUseCase(
        export_repo=mocked_export_repo,
        deployment_repo=deployment_repo,
        file_storage=MagicMock(),
        organization_repo=MagicMock(),
        auth_repo=MagicMock(),
    )
    return use_case


def get_deployment_repo(consent=None, econsent=None):
    deployment_repo = MagicMock()
    deployment_repo.retrieve_deployment.return_value = Deployment(
        id=SAMPLE_DEPLOYMENT_ID,
        consent=consent,
        econsent=econsent,
        code=DEPLOYMENT_CODE,
    )
    return deployment_repo


def get_export_repo():
    export_repo = MagicMock()
    users = [
        User(id=SIGNED_USER_ID, enrollmentId=100),
        User(id=NOT_SIGNED_USER_ID),
        User(id=NOT_SIGNED_LATEST_USER_ID),
    ]
    export_repo.retrieve_users.return_value = users
    export_repo.retrieve_consent_logs.return_value = [CONSENT_LOG]
    export_repo.retrieve_econsent_logs.return_value = [ECONSENT_LOG]
    export_repo.retrieve_export_profile.side_effect = ObjectDoesNotExist

    return export_repo
