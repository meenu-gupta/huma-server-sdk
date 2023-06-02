from sdk.common.exceptions.exceptions import (
    InvalidProjectIdException,
    InvalidClientIdException,
)
from sdk.common.utils import inject
from sdk.phoenix.config.server_config import PhoenixServerConfig, Project


def validate_project_id(project_id: str, project: Project = None):
    if not project:
        project = inject.instance(PhoenixServerConfig).server.project

    if project_id != project.id:
        raise InvalidProjectIdException
    return True


def validate_client_id(client_id, project: Project = None):
    if not project:
        project = inject.instance(PhoenixServerConfig).server.project

    client = project.get_client_by_id(client_id)
    if client is None:
        raise InvalidClientIdException
    return True


def validate_project_and_client_id(
    client_id: str, project_id: str, project: Project = None
):
    return validate_project_id(project_id, project) and validate_client_id(
        client_id, project
    )
