from extensions.module_result.event_bus.base_primitive_event import BasePrimitiveEvent


class PostCreatePrimitiveEvent(BasePrimitiveEvent):

    def __init__(self, **kwargs):
        super(PostCreatePrimitiveEvent, self).__init__(**kwargs)
        self.id = self.kwargs.pop("id")
        self.create_date_time = self.kwargs.pop("create_date_time")
