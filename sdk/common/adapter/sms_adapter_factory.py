from sdk.common.utils import inject
from sdk.phoenix.config.server_config import Adapters


class SMSAdapterFactory:
    @staticmethod
    def get_sms_adapter(config_adapters: Adapters, phone_number: str):
        if phone_number.startswith("+86") and config_adapters.aliCloudSms:
            return inject.instance("aliCloudSmsVerificationAdapter")
        return inject.instance("twilioSmsVerificationAdapter")
