from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, required_field


@convertibleclass
class APNSPushConfig:
    # IOS Apns
    useSandbox: bool = field(default=False)
    teamId: str = required_field()
    bundleId: str = required_field()
    authKeyFilePath: str = required_field()
    authKeyId: str = required_field()
