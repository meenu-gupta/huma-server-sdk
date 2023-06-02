from sdk.auth.events.set_auth_attributes_events import PostSetAuthAttributesEvent
from sdk.auth.events.sign_out_event import SignOutEventV1
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.auth.helpers.auth_helpers import get_user
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.utils.inject import autoparams
from sdk.notification.services.notification_service import NotificationService


@autoparams("email_adapter", "repo")
def send_password_updated_email(
    event: PostSetAuthAttributesEvent,
    email_adapter: EmailConfirmationAdapter,
    repo: AuthRepository,
):
    if event.old_password:
        user = get_user(repo=repo, uid=event.user_id)
        if user.email:
            email_adapter.send_password_changed_email(user.email, locale=event.language)


@autoparams("email_adapter", "repo")
def send_phone_number_updated_email(
    event: PostSetAuthAttributesEvent,
    email_adapter: EmailConfirmationAdapter,
    repo: AuthRepository,
):
    if event.mfa_phone_number_updated:
        user = get_user(repo=repo, uid=event.user_id)
        if user.email:
            email_adapter.send_mfa_phone_number_updated_email(
                user.email, locale=event.language
            )


def unregister_device_notifications(event: SignOutEventV1):
    if event.device_push_id or event.voip_device_push_id:
        svc = NotificationService()
        svc.unregister_device(
            user_id=event.userId,
            device_push_id=event.device_push_id,
            voip_device_push_id=event.voip_device_push_id,
        )
