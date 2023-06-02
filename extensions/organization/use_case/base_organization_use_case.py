from extensions.exceptions import (
    OrganizationDoesNotExist,
    DuplicateOrganizationNameException,
)
from extensions.organization.repository.organization_repository import (
    OrganizationRepository,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BaseOrganizationUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: OrganizationRepository):
        self.repo = repo

    def process_request(self, request_object):
        raise NotImplementedError

    def _validate_no_organization_with_same_name(self, organization_name: str):
        try:
            self.repo.retrieve_organization_by_name(organization_name)
        except OrganizationDoesNotExist:
            pass
        else:
            raise DuplicateOrganizationNameException
