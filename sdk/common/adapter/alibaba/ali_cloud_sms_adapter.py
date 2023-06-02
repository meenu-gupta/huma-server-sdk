import json

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from sdk.common.adapter.alibaba.ali_cloud_sms_config import AliCloudSmsConfig
from sdk.common.adapter.alibaba.exception import SendAlibabaSmsException
from sdk.common.adapter.sms_adapter import SmsAdapter


class AliCloudSmsAdapter(SmsAdapter):
    """
    how to configure it:
    > aliCloudSms:
    >   accessKeyId: !ENV ${MP_ALI_CLOUD_ACCESS_KEY_ID}
    >   accessKeySecret: !ENV ${MP_ALI_CLOUD_ACCESS_KEY_SECRET}
    >   params:
    >     region: cn-beijing
    >     domain: sms-intl.ap-southeast-1.aliyuncs.com
    >     fromId: 迈达普
    >     templateCode: SMS_10585524
    how to use it: (text should be six digits and the phone should be chinese, at least for now)
    > send: SmsAdapter = inject.instance('aliCloudSmsAdapter')
    > send.send_sms("+8618621320546", "121212", "")
    """

    def __init__(self, config: AliCloudSmsConfig):
        self._config = config
        self._client = AcsClient(
            self._config.accessKeyId,
            self._config.accessKeySecret,
            self._config.params.region,
        )

    def send_sms(
        self, phone_number: str, text: str, phone_number_source: str
    ) -> object:
        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain(self._config.params.domain)
        request.set_method("POST")
        request.set_version("2018-05-01")
        request.set_action_name("SendMessageWithTemplate")
        request.add_query_param("To", phone_number[1:])
        request.add_query_param("From", self._config.params.fromId)
        request.add_query_param("TemplateCode", self._config.params.templateCode)
        request.add_query_param("TemplateParam", json.dumps({"code": text}))
        request.add_query_param("SmsUpExtendCode", "12345")
        response = self._client.do_action_with_exception(request)
        json_response = json.loads(response.decode("utf-8"))
        if json_response["ResponseCode"] != "OK":
            raise SendAlibabaSmsException

        return ""
