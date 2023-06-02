from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class AzureBlobStorageConfig:
    connectionString: str = required_field()
