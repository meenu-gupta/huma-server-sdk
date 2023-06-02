from extensions.dashboard.models.gadgets import Gadget
from extensions.dashboard.router.dashboard_requests import (
    RetrieveGadgetDataRequestObject,
)
from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase


class RetrieveGadgetDataUseCase(UseCase):
    def process_request(self, request_object: RetrieveGadgetDataRequestObject):
        config_data = request_object.to_dict(ignored_fields=[request_object.SUBMITTER])
        gadget = Gadget.create_from_dict(
            data={Gadget.CONFIGURATION: config_data},
            gadget_type=request_object.gadgetId.value,
        )
        gadget.update_data()
        return Response(value=gadget)
