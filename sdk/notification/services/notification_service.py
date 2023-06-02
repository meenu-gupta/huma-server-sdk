import logging
from datetime import datetime
from typing import Optional, NamedTuple

from sdk.celery.app import celery_app
from sdk.common.adapter.fcm.fcm_push_adapter import FCMPushAdapter
from sdk.common.adapter.apns.apns_push_adapter import APNSPushAdapter
from sdk.common.adapter.alibaba.ali_cloud_push_adaptor import AliCloudPushAdapter
from sdk.common.adapter.push_notification_adapter import (
    AndroidMessage,
    ApnsMessage,
    AliCloudMessage,
    PushAdapter,
    VoipApnsMessage,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.notification.model.device import Device, PushIdType
from sdk.notification.repository.notification_repository import NotificationRepository
from sdk.phoenix.config.server_config import PhoenixServerConfig

logger = logging.getLogger(__name__)


class NotificationService:
    @autoparams()
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    def register_device(self, device: Device) -> str:
        device.createDateTime = device.updateDateTime = datetime.utcnow()
        return self.repo.register_device(device)

    def unregister_device(
        self, user_id: str, device_push_id: str = None, voip_device_push_id: str = None
    ) -> str:
        return self.repo.unregister_device(user_id, device_push_id, voip_device_push_id)

    def retrieve_devices(self, user_id: str) -> list[Device]:
        return self.repo.retrieve_devices(user_id)

    def push_for_user(
        self,
        user_id: str,
        android: AndroidMessage = None,
        ios: ApnsMessage = None,
        ali_cloud: AliCloudMessage = None,
        ttl: Optional[int] = None,
        run_async=True,
    ):
        logger.info(f"Push notification in service for user_id {user_id}")
        args = [
            user_id,
            android.to_dict(include_none=False) if android else None,
            ios.to_dict(include_none=False) if ios else None,
            ali_cloud.to_dict(include_none=False) if ali_cloud else None,
            ttl,
        ]
        if run_async:
            async_push_for_user.delay(*args)
        else:
            async_push_for_user(*args)

    def push_for_voip_user(
        self,
        user_id: str,
        android: AndroidMessage = None,
        ios_voip: VoipApnsMessage = None,
        ttl: Optional[int] = None,
    ) -> None:
        logger.info(f"Sending voip push notification to #userId{user_id}")
        async_push_for_voip_user_task.delay(
            user_id,
            android.to_dict(include_none=False) if android else None,
            ios_voip.to_dict(include_none=False) if ios_voip else None,
            ttl,
        )


class DeviceTypeGroup(NamedTuple):
    push: PushAdapter
    device_msg: dict
    ttl: Optional[int]
    devices: list[str] = []


@celery_app.task
def async_push_for_user(
    user_id: str,
    android_dict: dict = None,
    ios_dict: dict = None,
    ali_cloud_dict: dict = None,
    ttl: Optional[int] = None,
):
    logger.info(f"Push notification in task for user_id {user_id}")
    repo = inject.instance(NotificationRepository)
    config = inject.instance(PhoenixServerConfig)
    devices = repo.retrieve_devices(user_id)
    logger.info(f"{len(devices)} devices retrieved for user")
    groups_by_device = [
        _init_android_group(android_dict, config, ttl, devices),
        _init_ios_group(ios_dict, config, ttl, devices),
        _init_ali_group(ali_cloud_dict, config, ttl, devices),
    ]
    for group in groups_by_device:
        _push_for_device(repo, user_id, group)


@celery_app.task
def async_push_for_voip_user_task(
    user_id: str,
    android_dict: dict = None,
    ios_voip_dict: dict = None,
    ttl: Optional[int] = 45,
):
    logger.info(f"push for calling user_id {user_id}")
    repo = inject.instance(NotificationRepository)
    config = inject.instance(PhoenixServerConfig)
    devices = repo.retrieve_devices(user_id)
    logger.info(f"{len(devices)} devices retrieved for user")
    groups_by_device = [
        _init_android_group(android_dict, config, ttl, devices),
        _init_ios_voip_group(ios_voip_dict, config, ttl, devices),
    ]
    for group in groups_by_device:
        _push_for_device(repo, user_id, group)


def _init_android_group(android_dict, config, ttl, user_devices):
    if not (android_dict and config.server.adapters.fcmPush):
        return
    devices = [
        device
        for device in user_devices
        if device.devicePushIdType == PushIdType.ANDROID_FCM
    ]
    android_push: FCMPushAdapter = inject.instance("fcmPushAdapter")
    return DeviceTypeGroup(
        push=android_push,
        device_msg=AndroidMessage.from_dict(android_dict),
        ttl=ttl,
        devices=devices,
    )


def _init_ios_group(ios_dict, config, ttl, user_devices):
    if not (ios_dict and config.server.adapters.apnsPush):
        return
    devices = [
        device
        for device in user_devices
        if device.devicePushIdType == PushIdType.IOS_APNS
    ]
    ios_push: APNSPushAdapter = inject.instance("apnsPushAdapter")
    return DeviceTypeGroup(
        push=ios_push,
        device_msg=ApnsMessage.from_dict(ios_dict),
        ttl=ttl,
        devices=devices,
    )


def _init_ios_voip_group(ios_voip_dict, config, ttl, user_devices):
    if not (ios_voip_dict and config.server.adapters.apnsPush):
        return
    devices = [
        device
        for device in user_devices
        if device.devicePushIdType == PushIdType.IOS_VOIP
    ]
    ios_push: APNSPushAdapter = inject.instance("apnsPushAdapter")
    return DeviceTypeGroup(
        push=ios_push,
        device_msg=VoipApnsMessage.from_dict(ios_voip_dict),
        ttl=ttl,
        devices=devices,
    )


def _init_ali_group(ali_cloud_dict, config, ttl, user_devices):
    if not (ali_cloud_dict and config.server.adapters.aliCloudPush):
        return
    devices = [
        device
        for device in user_devices
        if device.devicePushIdType == PushIdType.ALI_CLOUD
    ]
    ali_cloud_push: AliCloudPushAdapter = inject.instance("aliCloudPushAdapter")
    return DeviceTypeGroup(
        push=ali_cloud_push,
        device_msg=AliCloudMessage.from_dict(ali_cloud_dict),
        ttl=ttl,
        devices=devices,
    )


def _push_for_device(repo, user_id, device_specs):
    if not device_specs:
        return
    if not device_specs.devices:
        logger.info(f"No {type(device_specs.push).__name__} devices for user#{user_id}")
        return
    try:
        ids_to_remove = device_specs.push.send_message_to_identities(
            [device.devicePushId for device in device_specs.devices],
            message=device_specs.device_msg,
            ttl=device_specs.ttl,
        )
        if not ids_to_remove:
            return
        repo.delete_devices(ids_to_remove)
        logger.info(
            f"{len(ids_to_remove)} {type(device_specs.push).__name__} devices were removed for user#{user_id}"
        )
    except Exception as e:
        logger.warning(f"Message failure for user#{user_id} due to {e}")
