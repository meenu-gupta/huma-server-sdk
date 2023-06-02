from extensions.authorization.events.get_badges_event import GetUserBadgesEvent
from extensions.export_deployment.repository.export_deployment_repository import (
    ExportDeploymentRepository,
)
from sdk.common.utils.inject import autoparams


@autoparams("repo")
def get_async_export_badges(
    event: GetUserBadgesEvent, repo: ExportDeploymentRepository
):
    count = repo.retrieve_unseen_export_process_count(event.user_id)
    return {"downloads": count}
