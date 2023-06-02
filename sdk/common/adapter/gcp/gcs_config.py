from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class GCSConfig:
    SERVICE_ACCOUNT_KEY_FILE_PATH = "serviceAccountKeyFilePath"

    serviceAccountKeyFilePath: str = required_field()
