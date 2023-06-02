from sdk.common.usecase.response_object import Response
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams
from sdk.versioning.models.version import Version
from sdk.versioning.router.versioning_requests import IncreaseVersionRequestObject


class IncreaseVersionUseCase(UseCase):
    @autoparams()
    def __init__(self, version: Version):
        self._version = version

    def process_request(self, request_object: IncreaseVersionRequestObject):
        if request_object.serverVersion:
            self._version.server = request_object.serverVersion

        if request_object.apiVersion:
            self._version.api = request_object.apiVersion

        return Response()
