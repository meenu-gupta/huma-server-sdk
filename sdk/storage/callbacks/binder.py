from sdk.common.adapter.event_bus_adapter import BaseEvent

class PostStorageSetupEvent(BaseEvent):
    pass

class BaseStorageEvent(BaseEvent):
    bucket = None
    object_name = None
    claims = None

    def __init__(self, bucket, object_name, claims):
        self.bucket = bucket
        self.object_name = object_name
        self.claims = claims
