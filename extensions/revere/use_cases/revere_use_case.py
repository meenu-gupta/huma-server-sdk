from extensions.revere.models.revere import RevereTestResult

from extensions.revere.router.revere_request_objects import (
    ProcessAudioResultRequestObject,
)
from extensions.revere.service.revere_service import RevereTestService
from sdk.common.usecase.use_case import UseCase


class UploadAudioResultUseCaseUseCase(UseCase):
    def process_request(self, request_object: ProcessAudioResultRequestObject):
        service = RevereTestService()
        result_words, extra_info = service.process_audio_result(
            request_object.audioResult
        )
        result = RevereTestResult.from_dict(
            {
                **request_object.to_dict(include_none=False),
                **extra_info,
                RevereTestResult.WORDS_RESULT: result_words,
            }
        )
        service.save_word_list_result(
            request_object.testId, request_object.submitterId, result
        )
