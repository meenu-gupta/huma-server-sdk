from extensions.authorization.events import (
    GetDeploymentCustomRoleEvent,
    GetOrganizationCustomRoleEvent,
)
from sdk.common.adapter.event_bus_adapter import EventBusAdapter
from sdk.common.utils.inject import autoparams


@autoparams("event_bus")
def get_deployment_custom_role(
    role_id: str, resource_id: str, event_bus: EventBusAdapter
):
    event = GetDeploymentCustomRoleEvent(role_id, resource_id)
    result = event_bus.emit(event)
    return result[-1] if result else None


@autoparams("event_bus")
def get_organization_custom_role(
    role_id: str, resource_id: str, event_bus: EventBusAdapter
):
    event = GetOrganizationCustomRoleEvent(role_id, resource_id)
    result = event_bus.emit(event)
    return result[-1] if result else None


def get_custom_role(role_id: str, resource_id: str, resource: str = None):
    if resource in ("deployment", None):
        role = get_deployment_custom_role(role_id, resource_id)
        if role:
            return role

    if resource in ("organization", None):
        return get_organization_custom_role(role_id, resource_id)
