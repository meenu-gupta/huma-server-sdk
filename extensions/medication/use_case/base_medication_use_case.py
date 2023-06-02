from extensions.medication.repository.medication_repository import (
    MedicationRepository,
)
from sdk.common.usecase.use_case import UseCase
from sdk.common.utils.inject import autoparams


class BaseMedicationUseCase(UseCase):
    @autoparams()
    def __init__(self, repo: MedicationRepository):
        self._repo = repo

    def process_request(self, request_object):
        raise NotImplementedError
