from extensions.kardia.repository.kardia_integration_client import (
    KardiaIntegrationClient,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BaseKardiaUseCase(UseCase):
    @autoparams("client")
    def __init__(self, client: KardiaIntegrationClient):
        self._kardia_integration_client = client

    def process_request(self, request_object):
        raise NotImplementedError
