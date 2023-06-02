from extensions.deployment.models.deployment import Deployment
from sdk.common.adapter.event_bus_adapter import BaseEvent


class BaseDeploymentEvent(BaseEvent):
    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id


class CreateDeploymentEvent(BaseDeploymentEvent):
    pass


class DeleteDeploymentEvent(BaseDeploymentEvent):
    pass


class BasePostKeyActionConfigEvent(BaseEvent):
    def __init__(self, key_action_config_id: str, deployment_id: str):
        self.key_action_config_id = key_action_config_id
        self.deployment_id = deployment_id


class PostCreateKeyActionConfigEvent(BasePostKeyActionConfigEvent):
    pass


class PostUpdateKeyActionConfigEvent(BasePostKeyActionConfigEvent):
    pass


class PostDeleteKeyActionConfigEvent(BaseEvent):
    def __init__(self, id: str):
        self.id = id


class PreDeploymentUpdateEvent(BaseEvent):
    def __init__(self, deployment=None, previous_state=None):
        self.deployment: Deployment = deployment
        self.previous_state: Deployment = previous_state


class PostDeploymentUpdateEvent(PreDeploymentUpdateEvent):
    pass


class TargetConsentedUpdateEvent(BaseEvent):
    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id
