import argparse
import os
import sys

from dotenv import load_dotenv

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../..")))

from extensions.authorization.adapters.email_invitation_adapter import (
    EmailInvitationAdapter,
)
from extensions.authorization.callbacks import setup_storage_auth
from extensions.authorization.component import AuthorizationComponent
from extensions.config.config import ExtensionServerConfig
from extensions.identity_verification.component import IdentityVerificationComponent
from sdk.auth.component import AuthComponent
from sdk.auth.enums import SendVerificationTokenMethod
from sdk.common.adapter.email_confirmation_adapter import EmailConfirmationAdapter
from sdk.common.adapter.email_verification_adapter import EmailVerificationAdapter
from sdk.common.adapter.identity_verification_mail_adapter import (
    IdentityVerificationEmailAdapter,
)
from sdk.common.localization.utils import Language
from sdk.common.utils import inject
from sdk.phoenix.component_manager import PhoenixComponentManager
from sdk.phoenix.config.server_config import Client
from sdk.phoenix.server import PhoenixServer
from sdk.storage.callbacks.binder import PostStorageSetupEvent

SERVER = "server"
WORKER = "worker"
BEAT = "beat"
RUN_CHOICES = [SERVER, WORKER, BEAT]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send email CLI")
    parser.add_argument(
        "--email", type=str, help="email to send email to", required=True
    )
    parser.add_argument("--option", type=int, help="option to run [1-9]", default=6)
    parser.add_argument(
        "--config", type=str, help="yaml config path", default="config.dev.yaml"
    )
    parser.add_argument(
        "--dotenv", type=str, help="dotenv file path", default="dev.env"
    )
    parser.add_argument(
        "--prod", type=bool, help="enable wsgi for production mode", default=False
    )
    parser.add_argument(
        "--set",
        action="append",
        type=lambda kv: kv.split("="),
        help="Argument which should be overridden in config."
        " Example: --set server.authorization.enable=false --set server.deployment.enable=false",
        default=None,
        dest="override_mapping",
    )
    args = parser.parse_args()

    # get dotenv path and load
    dotenv_path = os.path.join(here, args.dotenv)
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    conf_path = os.path.join(here, args.config)
    loc_path = os.path.join(here, "localization")
    override_mapping: dict[str, str] = dict(args.override_mapping or {})

    # setup config object to use in server and components
    phoenix_cfg = ExtensionServerConfig.get(conf_path, override_mapping)
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        IdentityVerificationComponent(),
    ]

    component_manager = PhoenixComponentManager()
    component_manager.register_components(components)

    phoenix_server = PhoenixServer(
        config=phoenix_cfg,
        localization_path=loc_path,
        component_manager=component_manager,
    )

    phoenix_server.event_bus.subscribe(PostStorageSetupEvent, setup_storage_auth)
    project_config = phoenix_server.config.server.project
    web_client = project_config.get_client_by_client_type(Client.ClientType.MANAGER_WEB)
    ios_client = project_config.get_client_by_client_type(Client.ClientType.USER_IOS)

    opt = args.option
    if opt == 1:
        # verify email ios
        adapter = inject.instance(EmailVerificationAdapter)
        adapter.send_verification_email(args.email, ios_client, "World", Language.EN)
    elif opt == 2:
        # verify email web
        adapter = inject.instance(EmailVerificationAdapter)
        adapter.send_verification_email(args.email, web_client, "World", Language.EN)
    elif opt == 3:
        # confirm sign up email ios & web ( no different )
        adapter = inject.instance(EmailConfirmationAdapter)
        adapter.send_confirmation_email(
            args.email,
            "Mr Backend",
            ios_client,
            SendVerificationTokenMethod.EMAIL_SIGNUP_CONFIRMATION,
            Language.EN,
        )
    elif opt == 4:
        # confirm sign up email ios & web for existing users ( no different )
        adapter = inject.instance(EmailConfirmationAdapter)
        adapter.send_confirmation_email(
            args.email,
            "Mr Backend",
            web_client,
            SendVerificationTokenMethod.EXISTING_USER_EMAIL_CONFIRMATION,
            Language.EN,
        )
    elif opt == 5:
        # confirm sign up email ios & web for existing users ( no different )
        adapter = inject.instance(EmailConfirmationAdapter)
        adapter.send_reset_password_email(args.email, web_client, Language.EN)
    elif opt == 6:
        # confirm sign up email ios & web for existing users ( no different )
        adapter = inject.instance(IdentityVerificationEmailAdapter)
        adapter.send_verification_result_email(args.email, "User1", Language.EN)
    elif opt == 7:
        # confirm sign up email ios & web for existing users ( no different )
        adapter = inject.instance(EmailInvitationAdapter)
        adapter.send_invitation_email(
            args.email, "Admin", web_client, Language.EN, "12345", "app@huma.com"
        )
    elif opt == 8:
        # confirm sign up email ios & web for existing users ( no different )
        adapter = inject.instance(EmailInvitationAdapter)
        adapter.send_invitation_email(
            args.email, "CLUB", web_client, Language.EN, "12345", "app@huma.com"
        )
    elif opt == 9:
        # confirm sign up email ios & web for existing users ( no different )
        adapter = inject.instance(EmailInvitationAdapter)
        adapter.send_role_update_email(
            args.email, web_client, Language.EN, "app@huma.com", 1
        )
    else:
        pass
