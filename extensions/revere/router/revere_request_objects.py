from extensions.common.s3object import S3Object
from extensions.module_result.models.primitives import Primitive
from extensions.revere.models.revere import RevereTest
from sdk import convertibleclass
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import must_be_present


@convertibleclass
class ProcessAudioResultRequestObject(Primitive):
    TEST_ID = "testId"

    audioResult: S3Object = required_field()
    initialWords: list[str] = required_field()
    testId: str = required_field()

    @classmethod
    def validate(cls, request):
        must_be_present(
            audioResult=request.audioResult, initialWords=request.initialWords
        )


@convertibleclass
class RetrieveUserTestsRequestObject:
    status: RevereTest.Status = default_field()


@convertibleclass
class ExportRevereResultsRequestObject:
    status: RevereTest.Status = default_field()
