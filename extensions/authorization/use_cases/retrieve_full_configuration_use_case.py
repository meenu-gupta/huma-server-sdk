from extensions.authorization.models.role.role import RoleName
from extensions.authorization.router.user_profile_request import (
    RetrieveFullConfigurationRequestObject,
)
from extensions.authorization.router.user_profile_response import (
    RetrieveFullConfigurationResponseObject,
)
from extensions.authorization.use_cases.base_authorization_use_case import (
    BaseAuthorizationUseCase,
)


class RetrieveFullConfigurationUseCase(BaseAuthorizationUseCase):
    SHOW_ORG_ROLES = (
        RoleName.DEPLOYMENT_STAFF,
        RoleName.CALL_CENTER,
        *RoleName.org_roles(),
    )

    def process_request(self, request_object: RetrieveFullConfigurationRequestObject):
        org_ids = request_object.user.organization_ids()
        deployment_ids = request_object.user.deployment_ids()
        organizations = self.retrieve_organizations(org_ids)

        if self.get_role_id() in self.SHOW_ORG_ROLES:
            for item in self.retrieve_organizations(deployment_ids=deployment_ids):
                if item.id in org_ids:
                    continue
                organizations.append(item)
        deployments = self.deployment_repo.retrieve_deployments_by_ids(deployment_ids)
        for deployment in deployments:
            deployment.preprocess_for_configuration()
        language = request_object.user.user.language
        return RetrieveFullConfigurationResponseObject(
            organizations, deployments, language
        )

    def retrieve_organizations(
        self, ids: list[str] = None, deployment_ids: list[str] = None
    ):
        organizations = []
        kwargs = {}
        if ids:
            kwargs.update({"ids": ids})
        if deployment_ids:
            kwargs.update({"deployment_ids": deployment_ids})
        if kwargs:
            organizations, _ = self.organization_repo.retrieve_organizations(**kwargs)

        for org in organizations:
            org.set_presigned_urls_for_legal_docs()
        return organizations

    def get_role_id(self):
        return self.request_object.user.get_role().id
