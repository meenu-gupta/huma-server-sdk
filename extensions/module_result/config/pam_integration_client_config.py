from sdk.common.utils.convertible import convertibleclass, meta, default_field


@convertibleclass
class PAMIntegrationClientConfig:
    submitSurveyURI: str = default_field()
    enrollUserURI: str = default_field()
    clientExtID: str = default_field()
    clientPassKey: str = default_field()
    subgroupExtID: str = default_field()
    timeout: int = default_field(metadata=meta(lambda x: x is None or 0 < x))
