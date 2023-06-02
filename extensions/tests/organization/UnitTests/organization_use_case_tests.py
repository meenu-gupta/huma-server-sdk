from unittest import TestCase
from unittest.mock import MagicMock, patch

from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.status import Status
from extensions.exceptions import OrganizationDoesNotExist
from extensions.organization.models.organization import Organization
from extensions.organization.router.organization_requests import (
    CreateOrganizationRequestObject,
    UpdateOrganizationRequestObject,
    RetrieveOrganizationRequestObject,
    DeleteOrganizationRequestObject,
    RetrieveOrganizationsRequestObject,
    UnlinkDeploymentRequestObject,
    LinkDeploymentRequestObject,
    LinkDeploymentsRequestObject,
    UnlinkDeploymentsRequestObject,
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.create_organization_use_case import (
    CreateOrganizationUseCase,
)
from extensions.organization.use_case.delete_organization_use_case import (
    DeleteOrganizationUseCase,
)
from extensions.organization.use_case.link_deployment_use_case import (
    LinkDeploymentUseCase,
)
from extensions.organization.use_case.link_deployments_use_case import (
    LinkDeploymentsUseCase,
)
from extensions.organization.use_case.retrieve_organization_use_case import (
    RetrieveOrganizationUseCase,
)
from extensions.organization.use_case.retrieve_organizations_use_case import (
    RetrieveOrganizationsUseCase,
)
from extensions.organization.use_case.unlink_deployment_use_case import (
    UnlinkDeploymentUseCase,
)
from extensions.organization.use_case.unlink_deployments_use_case import (
    UnlinkDeploymentsUseCase,
)
from extensions.organization.use_case.update_organization_use_case import (
    UpdateOrganizationUseCase,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils import inject
from sdk.common.utils.convertible import ConvertibleClassValidationError

SAMPLE_ORGANIZATION_ID = "5ffea8e41d3eaea109cd0773"
SAMPLE_ORGANIZATION_NAME = "Test Organization"

SAMPLE_DEPLOYMENT_ID = "5e84b0dab8dfa268b1180536"
USE_CASE_ROUTE = "extensions.organization.use_case"


class MockDeploymentService:
    retrieve_deployment = MagicMock(
        return_value=Deployment(name="Deployment", id=SAMPLE_DEPLOYMENT_ID)
    )
    retrieve_deployments_by_ids = MagicMock(return_value=[])


class TestOrganizationUseCase(TestCase):
    def setUp(self) -> None:
        self.mocked_organization_repo = MagicMock()

        def bind_and_configure(binder):
            binder.bind(EventBusAdapter, MagicMock())

        inject.clear_and_configure(bind_and_configure)

    def test_create_organization(self):
        self.mocked_organization_repo.retrieve_organization_by_name.side_effect = (
            OrganizationDoesNotExist()
        )

        request_object = CreateOrganizationRequestObject(name=SAMPLE_ORGANIZATION_NAME)
        CreateOrganizationUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.retrieve_organization_by_name.assert_called_with(
            SAMPLE_ORGANIZATION_NAME
        )
        self.mocked_organization_repo.create_organization.assert_called_with(
            organization=request_object
        )

    def test_update_organization(self):
        self.mocked_organization_repo.retrieve_organization_by_name.side_effect = (
            OrganizationDoesNotExist()
        )

        request_object = UpdateOrganizationRequestObject(
            id=SAMPLE_ORGANIZATION_ID, name=SAMPLE_ORGANIZATION_NAME
        )
        UpdateOrganizationUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.retrieve_organization_by_name.assert_called_with(
            SAMPLE_ORGANIZATION_NAME
        )
        self.mocked_organization_repo.update_organization.assert_called_with(
            organization=request_object
        )

    def test_retrieve_organization(self):
        request_object = RetrieveOrganizationRequestObject(
            organizationId=SAMPLE_ORGANIZATION_ID
        )
        RetrieveOrganizationUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.retrieve_organization_with_deployment_data.assert_called_with(
            organization_id=SAMPLE_ORGANIZATION_ID
        )

    def test_retrieve_organizations(self):
        self.mocked_organization_repo.retrieve_organizations.return_value = (
            [Organization(name=SAMPLE_ORGANIZATION_NAME)],
            1,
        )
        request_object = RetrieveOrganizationsRequestObject(skip=0, limit=10)
        RetrieveOrganizationsUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.retrieve_organizations.assert_called_with(
            skip=0,
            limit=10,
            name_contains=None,
            sort_fields=None,
            search_criteria=None,
            status=None,
        )

    def test_delete_organization(self):
        request_object = DeleteOrganizationRequestObject(
            organizationId=SAMPLE_ORGANIZATION_ID
        )
        DeleteOrganizationUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.delete_organization.assert_called_with(
            organization_id=SAMPLE_ORGANIZATION_ID
        )

    @patch(
        f"{USE_CASE_ROUTE}.link_deployment_use_case.DeploymentService",
        MockDeploymentService,
    )
    @patch(
        f"{USE_CASE_ROUTE}.link_deployment_use_case.UpdateOrganizationTargetConsentedUseCase"
    )
    def test_link_deployment(self, consented_use_case):
        request_object = LinkDeploymentRequestObject(
            organizationId=SAMPLE_ORGANIZATION_ID, deploymentId=SAMPLE_DEPLOYMENT_ID
        )
        LinkDeploymentUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.link_deployment.assert_called_with(
            organization_id=SAMPLE_ORGANIZATION_ID, deployment_id=SAMPLE_DEPLOYMENT_ID
        )
        consented_use_case().execute.assert_called_with(
            UpdateOrganizationTargetConsentedRequestObject(
                organizationIds=None, organizationId=SAMPLE_ORGANIZATION_ID
            )
        )

    @patch(
        f"{USE_CASE_ROUTE}.unlink_deployment_use_case.UpdateOrganizationTargetConsentedUseCase"
    )
    def test_unlink_deployment(self, consented_use_case):
        request_object = UnlinkDeploymentRequestObject(
            organizationId=SAMPLE_ORGANIZATION_ID, deploymentId=SAMPLE_DEPLOYMENT_ID
        )
        UnlinkDeploymentUseCase(repo=self.mocked_organization_repo).execute(
            request_object
        )
        self.mocked_organization_repo.unlink_deployment.assert_called_with(
            organization_id=SAMPLE_ORGANIZATION_ID, deployment_id=SAMPLE_DEPLOYMENT_ID
        )
        consented_use_case().execute.assert_called_with(
            UpdateOrganizationTargetConsentedRequestObject(
                organizationIds=None, organizationId=SAMPLE_ORGANIZATION_ID
            )
        )


class TestOrganizationRequestObject(TestCase):
    def test_failure_create_organization_invalid_name(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrganizationRequestObject.from_dict(
                {CreateOrganizationRequestObject.NAME: None}
            )

    def test_failure_create_organization_with_deployments(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrganizationRequestObject.from_dict(
                {
                    CreateOrganizationRequestObject.NAME: "Test Org",
                    CreateOrganizationRequestObject.DEPLOYMENT_IDS: [
                        "5e84b0dab8dfa268b1180536"
                    ],
                }
            )

    def test_failure_create_organization_no_name(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrganizationRequestObject.from_dict(
                {
                    CreateOrganizationRequestObject.STATUS: Status.DEPLOYED,
                }
            )

    def test_failure_create_organization_wrong_status(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrganizationRequestObject.from_dict(
                {
                    CreateOrganizationRequestObject.NAME: "Test Organization",
                    CreateOrganizationRequestObject.STATUS: "ANSWERED",
                }
            )

    def test_failure_create_organization_invalid_deployment_ids(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrganizationRequestObject.from_dict(
                {
                    CreateOrganizationRequestObject.NAME: "Test Organization",
                    CreateOrganizationRequestObject.DEPLOYMENT_IDS: [
                        "5ffea8e41d3eaea109cd0773",
                        "aaa",
                    ],
                }
            )

    def test_failure_update_organization_no_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UpdateOrganizationRequestObject.from_dict(
                {
                    CreateOrganizationRequestObject.NAME: "Test Organization",
                }
            )

    def test_failure_update_organization_with_deployments(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CreateOrganizationRequestObject.from_dict(
                {
                    CreateOrganizationRequestObject.ID: "5e84b0dab8dfa268b1180538",
                    CreateOrganizationRequestObject.DEPLOYMENT_IDS: [
                        "5e84b0dab8dfa268b1180536"
                    ],
                }
            )

    def _sample_legal_org_fields(self, field_to_exclude: str) -> dict:
        data = {
            Organization.PRIVACY_POLICY_URL: "https://some_url.com/",
            Organization.TERM_AND_CONDITION_URL: "https://some_url.com/",
            Organization.EULA_URL: "https://some_url.com/",
        }
        data.pop(field_to_exclude)
        return data

    def _assert_failure_creation_without_legal_doc_url(self, field_to_check: str):
        legal_urls = self._sample_legal_org_fields(field_to_check)
        res = CreateOrganizationRequestObject(
            name=SAMPLE_ORGANIZATION_NAME, **legal_urls
        )
        with self.assertRaises(ConvertibleClassValidationError):
            res.validate(res)

    def test_failure_must_be_at_least_one_of__no_privacy_policy(self):
        self._assert_failure_creation_without_legal_doc_url(
            Organization.PRIVACY_POLICY_URL
        )

    def test_failure_must_be_at_least_one_of__no_term_and_condition(self):
        self._assert_failure_creation_without_legal_doc_url(
            Organization.TERM_AND_CONDITION_URL
        )

    def test_failure_must_be_at_least_one_of__no_eula(self):
        self._assert_failure_creation_without_legal_doc_url(Organization.EULA_URL)


class LinkDeploymentsTestCase(TestCase):
    def setUp(self) -> None:
        self.mocked_organization_repo = MagicMock()

    @patch(
        f"{USE_CASE_ROUTE}.link_deployments_use_case.DeploymentService",
        MockDeploymentService,
    )
    @patch(
        f"{USE_CASE_ROUTE}.link_deployment_use_case.DeploymentService",
        MockDeploymentService,
    )
    @patch(
        f"{USE_CASE_ROUTE}.link_deployments_use_case.UpdateOrganizationTargetConsentedUseCase"
    )
    def test_success_process_request_link_deployments(self, consented_use_case):
        req_obj = LinkDeploymentsRequestObject.from_dict(
            {
                LinkDeploymentsRequestObject.DEPLOYMENT_IDS: [SAMPLE_DEPLOYMENT_ID],
                LinkDeploymentsRequestObject.ORGANIZATION_ID: SAMPLE_ORGANIZATION_ID,
            }
        )
        LinkDeploymentsUseCase(repo=self.mocked_organization_repo).execute(req_obj)
        self.mocked_organization_repo.link_deployments.assert_called_with(
            organization_id=SAMPLE_ORGANIZATION_ID,
            deployment_ids=[SAMPLE_DEPLOYMENT_ID],
        )
        consented_use_case().execute.assert_called_with(
            UpdateOrganizationTargetConsentedRequestObject(
                organizationIds=None, organizationId=SAMPLE_ORGANIZATION_ID
            )
        )

    def test_success_create_link_deployment_req_obj(self):
        try:
            LinkDeploymentsRequestObject.from_dict(
                {
                    LinkDeploymentsRequestObject.DEPLOYMENT_IDS: [SAMPLE_DEPLOYMENT_ID],
                    LinkDeploymentsRequestObject.ORGANIZATION_ID: SAMPLE_ORGANIZATION_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_link_deployment__no_deployment_ids(self):
        with self.assertRaises(ConvertibleClassValidationError):
            LinkDeploymentsRequestObject.from_dict(
                {
                    LinkDeploymentsRequestObject.ORGANIZATION_ID: SAMPLE_ORGANIZATION_ID,
                }
            )

    def test_failure_create_link_deployment__no_org_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            LinkDeploymentsRequestObject.from_dict(
                {
                    LinkDeploymentsRequestObject.DEPLOYMENT_IDS: [SAMPLE_DEPLOYMENT_ID],
                }
            )


class UnlinkDeploymentsTestCase(LinkDeploymentsTestCase):
    @patch(
        f"{USE_CASE_ROUTE}.unlink_deployments_use_case.UpdateOrganizationTargetConsentedUseCase"
    )
    def test_success_process_request_unlink_deployments(self, consented_use_case):
        req_obj = UnlinkDeploymentsRequestObject.from_dict(
            {
                UnlinkDeploymentsRequestObject.DEPLOYMENT_IDS: [SAMPLE_DEPLOYMENT_ID],
                UnlinkDeploymentsRequestObject.ORGANIZATION_ID: SAMPLE_ORGANIZATION_ID,
            }
        )
        UnlinkDeploymentsUseCase(repo=self.mocked_organization_repo).execute(req_obj)
        self.mocked_organization_repo.unlink_deployments.assert_called_with(
            organization_id=SAMPLE_ORGANIZATION_ID,
            deployment_ids=[SAMPLE_DEPLOYMENT_ID],
        )
        consented_use_case().execute.assert_called_with(
            UpdateOrganizationTargetConsentedRequestObject(
                organizationIds=None, organizationId=SAMPLE_ORGANIZATION_ID
            )
        )

    def test_success_create_unlink_deployment_req_obj(self):
        try:
            UnlinkDeploymentsRequestObject.from_dict(
                {
                    UnlinkDeploymentsRequestObject.DEPLOYMENT_IDS: [
                        SAMPLE_DEPLOYMENT_ID
                    ],
                    UnlinkDeploymentsRequestObject.ORGANIZATION_ID: SAMPLE_ORGANIZATION_ID,
                }
            )
        except ConvertibleClassValidationError:
            self.fail()

    def test_failure_create_unlink_deployment__no_deployments_ids(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UnlinkDeploymentsRequestObject.from_dict(
                {
                    UnlinkDeploymentsRequestObject.ORGANIZATION_ID: SAMPLE_ORGANIZATION_ID,
                }
            )

    def test_failure_create_unlink_deployment__no_org_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            UnlinkDeploymentsRequestObject.from_dict(
                {
                    UnlinkDeploymentsRequestObject.DEPLOYMENT_IDS: [
                        SAMPLE_DEPLOYMENT_ID
                    ],
                }
            )
