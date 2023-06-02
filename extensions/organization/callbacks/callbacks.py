from extensions.deployment.events import TargetConsentedUpdateEvent
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from extensions.organization.router.organization_requests import (
    UpdateOrganizationTargetConsentedRequestObject,
)
from extensions.organization.use_case.update_organization_target_consented_use_case import (
    UpdateOrganizationTargetConsentedUseCase,
)
from sdk.common.utils.inject import autoparams


@autoparams("org_repo")
def process_target_consented_update(
    event: TargetConsentedUpdateEvent, org_repo: OrganizationRepository
):
    organization_ids = org_repo.retrieve_organization_ids([event.deployment_id])

    req_obj = UpdateOrganizationTargetConsentedRequestObject.from_dict(
        {
            UpdateOrganizationTargetConsentedRequestObject.ORGANIZATION_IDS: organization_ids
        }
    )
    UpdateOrganizationTargetConsentedUseCase().execute(req_obj)
