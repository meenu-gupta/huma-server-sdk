from dataclasses import dataclass

from sdk.common.adapter.event_bus_adapter import BaseEvent


@dataclass
class DeleteDeploymentCustomRolesEvent(BaseEvent):
    deleted_ids: list[str]
    deployment_id: str
