from sdk.common.adapter.event_bus_adapter import BaseEvent


class GetCustomRoleEvent(BaseEvent):
    def __init__(self, role_id: str, resource_id: str):
        self.role_id = role_id
        self.resource_id = resource_id


class GetDeploymentCustomRoleEvent(GetCustomRoleEvent):
    pass


class GetOrganizationCustomRoleEvent(GetCustomRoleEvent):
    pass
