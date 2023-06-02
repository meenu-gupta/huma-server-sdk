from unittest import TestCase
from unittest.mock import MagicMock

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.role.default_roles import DefaultRoles
from extensions.authorization.models.role.role import Role
from extensions.authorization.models.user import BoardingStatus, User, PersonalDocument
from extensions.authorization.router.user_profile_request import (
    AssignManagerRequestObject,
    OffBoardUserRequestObject,
    SystemOffBoardUserRequestObject,
    RetrieveAssignedProfilesRequestObject,
    RetrieveProfilesRequestObject,
    RetrieveFullConfigurationRequestObject,
    ReactivateUserRequestObject,
    RetrieveUserResourcesRequestObject,
    FinishUserOnBoardingRequestObject,
    SortParameters,
    UpdateUserProfileRequestObject,
    CreateHelperAgreementLogRequestObject,
    CreatePersonalDocumentRequestObject,
)
from extensions.common.s3object import S3Object
from extensions.deployment.models.deployment import Deployment
from extensions.tests.authorization.UnitTests.test_helpers import (
    get_sample_assign_manager_request,
)
from sdk.common.localization.utils import Language, Localization
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.inject import Binder

SAMPLE_CONFIG_ID = "5fe07f2c0d862378d70fa19b"
SAMPLE_USER_ID = "5fe07f2c0d862378d70fa19b"
SAMPLE_DETAILS_OFF_BOARDED = "Recovered"


class TestUpdateUserProfileRequestObject(TestCase):
    def test_validation(self):
        data = {"name": "Test"}
        try:
            UpdateUserProfileRequestObject.from_dict(data)
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_validation_email(self):
        data = {"email": "Test@test.com"}
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateUserProfileRequestObject.from_dict(data)


class TestAssignManagerRequestObjects(TestCase):
    def test_failure_no_user_id(self):
        request_obj = get_sample_assign_manager_request()
        request_obj.pop(AssignManagerRequestObject.USER_ID, None)
        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagerRequestObject.from_dict(request_obj)

    def test_failure_no_manager_ids(self):
        request_obj = get_sample_assign_manager_request()
        request_obj.pop(AssignManagerRequestObject.MANAGER_IDS, None)
        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagerRequestObject.from_dict(request_obj)

    def test_failure_no_submitter_id(self):
        request_obj = get_sample_assign_manager_request()
        request_obj.pop(AssignManagerRequestObject.SUBMITTER_ID, None)
        with self.assertRaises(ConvertibleClassValidationError):
            AssignManagerRequestObject.from_dict(request_obj)

    def test_success_create_assign_manager_request_object(self):
        request_object = AssignManagerRequestObject.from_dict(
            get_sample_assign_manager_request()
        )
        self.assertIsNotNone(request_object)


class TestRetrieveAssignedProfilesRequestObjects(TestCase):
    def test_failure_no_manager_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveAssignedProfilesRequestObject.from_dict({})

    def test_success_create_retrieve_assigned_profiles_request_object(self):
        request_object = RetrieveAssignedProfilesRequestObject.from_dict(
            {"managerId": "5fe07f2c0d862378d70fa19b"}
        )
        self.assertIsNotNone(request_object)


class TestRetrieveProfilesRequestObject(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def configure_with_binder(binder: Binder):
            binder.bind(DefaultRoles, DefaultRoles())

        inject.clear_and_configure(configure_with_binder)

    def test_failure_no_deployment_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveProfilesRequestObject.from_dict({})

    def test_success_create_retrieve_profiles_request_object(self):
        request_object = RetrieveProfilesRequestObject.from_dict(
            {
                RetrieveProfilesRequestObject.DEPLOYMENT_ID: "5fe07f2c0d862378d70fa19b",
                RetrieveProfilesRequestObject.SUBMITTER: AuthorizedUser(User()),
            }
        )
        self.assertIsNotNone(request_object)

    def test_has_sort_fields(self):
        req_obj = RetrieveProfilesRequestObject(
            sort=SortParameters(
                fields=[SortParameters.Field.FLAGS],
                order=SortParameters.Order.ASCENDING,
            )
        )
        self.assertTrue(req_obj.has_sort_fields())

    def test_has_sort_fields_no_order(self):
        req_obj = RetrieveProfilesRequestObject(
            sort=SortParameters(fields=[SortParameters.Field.FLAGS])
        )
        self.assertFalse(req_obj.has_sort_fields())

    def test_has_sort_fields_no_fields(self):
        req_obj = RetrieveProfilesRequestObject(
            sort=SortParameters(order=SortParameters.Order.ASCENDING)
        )
        self.assertFalse(req_obj.has_sort_fields())

    def test_has_sort_fields_no_sort(self):
        req_obj = RetrieveProfilesRequestObject()
        self.assertFalse(req_obj.has_sort_fields())

    def test_is_for_user(self):
        req_obj = RetrieveProfilesRequestObject(role=Role.UserType.USER)
        self.assertTrue(req_obj.is_for_users())

    def test_is_for_user_default_role(self):
        req_obj = RetrieveProfilesRequestObject()
        self.assertTrue(req_obj.is_for_users())

    def test_is_for_user_role_no_role(self):
        req_obj = RetrieveProfilesRequestObject(role=None)
        self.assertFalse(req_obj.is_for_users())

    def test_is_for_user_role_not_user(self):
        req_obj = RetrieveProfilesRequestObject(role=Role.UserType.MANAGER)
        self.assertFalse(req_obj.is_for_users())

    def test_is_complex_sort_request(self):
        req_obj = RetrieveProfilesRequestObject(
            sort=SortParameters(
                fields=[SortParameters.Field.RAG], order=SortParameters.Order.ASCENDING
            )
        )
        self.assertTrue(req_obj.is_complex_sort_request())

    def test_is_complex_sort_request_not_rag(self):
        req_obj = RetrieveProfilesRequestObject(
            sort=SortParameters(
                fields=[SortParameters.Field.FLAGS],
                order=SortParameters.Order.ASCENDING,
            )
        )
        self.assertFalse(req_obj.is_complex_sort_request())

    def test_is_complex_sort_request_not_sort(self):
        req_obj = RetrieveProfilesRequestObject()
        self.assertFalse(req_obj.is_complex_sort_request())


class TestRetrieveFullConfigurationRequestObject(TestCase):
    def test_failure_no_user_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveFullConfigurationRequestObject.from_dict({})


class TestReactivateUserRequestObject(TestCase):
    def test_success_reactivate_user_request_object(self):
        try:
            ReactivateUserRequestObject.from_dict(
                {
                    ReactivateUserRequestObject.USER_ID: SAMPLE_USER_ID,
                    ReactivateUserRequestObject.SUBMITTER_ID: SAMPLE_USER_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ReactivateUserRequestObject.from_dict({})

    def test_failure_invalid_object_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ReactivateUserRequestObject.from_dict(
                {
                    ReactivateUserRequestObject.USER_ID: "SAMPLE_USER_ID",
                    ReactivateUserRequestObject.SUBMITTER_ID: SAMPLE_USER_ID,
                }
            )


class TestOffBoardUserRequestObject(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def bind_and_configure(binder):
            binder.bind(Localization, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    def test_success_off_board_user_request_object(self):
        try:
            OffBoardUserRequestObject.from_dict(
                {
                    OffBoardUserRequestObject.USER_ID: SAMPLE_USER_ID,
                    OffBoardUserRequestObject.DEPLOYMENT: Deployment(),
                    OffBoardUserRequestObject.DETAILS_OFF_BOARDED: SAMPLE_DETAILS_OFF_BOARDED,
                    OffBoardUserRequestObject.SUBMITTER_ID: SAMPLE_USER_ID,
                    OffBoardUserRequestObject.LANGUAGE: Language.DE,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            OffBoardUserRequestObject.from_dict({})

    def test_failure_invalid_object_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            OffBoardUserRequestObject.from_dict(
                {
                    OffBoardUserRequestObject.USER_ID: SAMPLE_USER_ID,
                    OffBoardUserRequestObject.SUBMITTER_ID: "SAMPLE_USER_ID",
                }
            )

    def test_failure_off_board_user_missing_field_user_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            OffBoardUserRequestObject.from_dict(
                {OffBoardUserRequestObject.SUBMITTER_ID: SAMPLE_USER_ID}
            )

    def test_failure_off_board_user_missing_field_submitter_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            OffBoardUserRequestObject.from_dict(
                {OffBoardUserRequestObject.USER_ID: SAMPLE_USER_ID}
            )


class TestSystemOffBoardUserRequestObject(TestCase):
    def test_success_system_off_board_user_request_object(self):
        try:
            SystemOffBoardUserRequestObject.from_dict(
                {
                    SystemOffBoardUserRequestObject.USER_ID: SAMPLE_USER_ID,
                    SystemOffBoardUserRequestObject.REASON: BoardingStatus.ReasonOffBoarded.USER_NO_CONSENT,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_no_required_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SystemOffBoardUserRequestObject.from_dict({})

    def test_failure_invalid_reason(self):
        with self.assertRaises(ConvertibleClassValidationError):
            SystemOffBoardUserRequestObject.from_dict(
                {
                    SystemOffBoardUserRequestObject.USER_ID: SAMPLE_USER_ID,
                    SystemOffBoardUserRequestObject.REASON: 8,
                }
            )


class TestRetrieveUserResourcesRequestObject(TestCase):
    def test_success_retrieve_user_resources_req_obj(self):
        try:
            RetrieveUserResourcesRequestObject.from_dict(
                {RetrieveUserResourcesRequestObject.USER_ID: SAMPLE_USER_ID}
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_id_is_not_valid(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveUserResourcesRequestObject.from_dict(
                {RetrieveUserResourcesRequestObject.USER_ID: "SAMPLE_USER_ID"}
            )


class TestFinishUserOnBoardingRequestObject(TestCase):
    def test_success_finish_user_on_boarding_req_obj(self):
        try:
            FinishUserOnBoardingRequestObject.from_dict(
                {
                    FinishUserOnBoardingRequestObject.ID: SAMPLE_USER_ID,
                    FinishUserOnBoardingRequestObject.FINISHED_ONBOARDING: True,
                    FinishUserOnBoardingRequestObject.BOARDING_STATUS: BoardingStatus(
                        status=BoardingStatus.Status.ACTIVE
                    ),
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_invalid_field(self):
        with self.assertRaises(ConvertibleClassValidationError):
            FinishUserOnBoardingRequestObject.from_dict(
                {FinishUserOnBoardingRequestObject.ENROLLMENT_ID: 5}
            )


class TestSortParameters(TestCase):
    def test_success_sort_by_module(self):
        body = {
            "fields": ["MODULE"],
            "sort": "ASCENDING",
            "extra": {
                "moduleId": "testModule",
                "moduleConfigId": "61e0303f3547262976bd66bb",
            },
        }
        try:
            SortParameters.from_dict(body)
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_success_sort_by_flags(self):
        body = {
            "fields": ["FLAGS"],
            "sort": "ASCENDING",
        }
        try:
            SortParameters.from_dict(body)
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_failure_sort_by_flags_with_extra(self):
        body = {
            "fields": ["FLAGS"],
            "sort": "ASCENDING",
            "extra": {
                "moduleId": "testModule",
                "moduleConfigId": "61e0303f3547262976bd66bb",
            },
        }
        with self.assertRaises(ConvertibleClassValidationError):
            SortParameters.from_dict(body)

    def test_failure_sort_by_module_multiple_fields(self):
        body = {
            "fields": ["MODULE", "FLAGS"],
            "sort": "ASCENDING",
            "extra": {
                "moduleId": "testModule",
                "moduleConfigId": "61e0303f3547262976bd66bb",
            },
        }
        with self.assertRaises(ConvertibleClassValidationError):
            SortParameters.from_dict(body)

    def test_failure_sort_by_module_no_extra(self):
        body = {
            "fields": ["MODULE"],
            "sort": "ASCENDING",
        }
        with self.assertRaises(ConvertibleClassValidationError):
            SortParameters.from_dict(body)

    def test_failure_sort_by_module_extra_wrong_type(self):
        body = {"fields": ["MODULE"], "sort": "ASCENDING", "extra": "test"}
        with self.assertRaises(ConvertibleClassValidationError):
            SortParameters.from_dict(body)

    def test_failure_sort_by_module_no_module_id(self):
        body = {
            "fields": ["MODULE"],
            "sort": "ASCENDING",
            "extra": {"moduleConfigId": "61e0303f3547262976bd66bb"},
        }
        with self.assertRaises(ConvertibleClassValidationError):
            SortParameters.from_dict(body)

    def test_failure_sort_by_module_no_module_config_id(self):
        body = {
            "fields": ["MODULE"],
            "sort": "ASCENDING",
            "extra": {"moduleId": "testModule"},
        }
        with self.assertRaises(ConvertibleClassValidationError):
            SortParameters.from_dict(body)


class TestCreatePersonalDocumentRequestObject(TestCase):
    def test_to_personal_document(self):
        req_obj = CreatePersonalDocumentRequestObject(
            name="Test",
            fileType=PersonalDocument.PersonalDocumentMediaType.PDF,
            fileObject=S3Object(key="test", bucket="test"),
            userId="61e0303f3547262976bd66bb",
        )
        try:
            doc = req_obj.to_personal_document()
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

        self.assertEqual(req_obj.name, doc.name)
        self.assertEqual(req_obj.fileType, doc.fileType)


class TestCreateHelperAgreementLogRequestObject(TestCase):
    def sample(self):
        return {
            "userId": "61e0303f3547262976bd66bb",
            "deploymentId": "61e0303f3547262976bd66bb",
            "status": "AGREE_AND_ACCEPT",
        }

    def test_validation(self):
        try:
            CreateHelperAgreementLogRequestObject.from_dict(self.sample())
        except ConvertibleClassValidationError as error:
            self.fail(str(error))

    def test_validation_id(self):
        body = self.sample()
        body["id"] = "61e0303f3547262976bd66bb"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateHelperAgreementLogRequestObject.from_dict(body)

    def test_validation_create_date_time(self):
        body = self.sample()
        body["createDateTime"] = "2022-01-01T10:00:00.000Z"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateHelperAgreementLogRequestObject.from_dict(body)

    def test_validation_update_date_time(self):
        body = self.sample()
        body["updateDateTime"] = "2022-01-01T10:00:00.000Z"
        with self.assertRaises(ConvertibleClassValidationError):
            CreateHelperAgreementLogRequestObject.from_dict(body)
