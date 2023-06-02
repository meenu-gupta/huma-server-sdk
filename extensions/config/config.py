from dataclasses import field

from extensions.appointment.config.config import AppointmentConfig
from extensions.authorization.config.config import AuthorizationConfig
from extensions.authorization.config.invitation_config import (
    InvitationConfig,
)
from extensions.deployment.config.config import DeploymentConfig
from extensions.kardia.config.config import KardiaConfig
from extensions.key_action.component import KeyActionConfig
from extensions.medication.config.config import MedicationTrackerConfig
from extensions.module_result.config.config import ModuleResultConfig
from extensions.publisher.config.config import PublisherConfig
from extensions.reminder.config.config import UserModuleReminderConfig
from extensions.revere.config.config import RevereTestConfig
from extensions.export_deployment.config.config import ExportDeploymentConfig
from extensions.twilio_video.component import TwilioVideoConfig
from extensions.identity_verification.config.config import IdentityVerificationConfig

from sdk.common.utils.convertible import convertibleclass, required_field
from sdk.phoenix.config.server_config import PhoenixServerConfig, Server, Adapters


@convertibleclass
class ExtensionAdapters(Adapters):
    pass


@convertibleclass
class ExtensionServer(Server):
    appointment: AppointmentConfig = field(default_factory=AppointmentConfig)
    authorization: AuthorizationConfig = field(default_factory=AuthorizationConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    keyAction: KeyActionConfig = field(default_factory=KeyActionConfig)
    userModuleReminder: UserModuleReminderConfig = field(
        default_factory=UserModuleReminderConfig
    )
    moduleResult: ModuleResultConfig = field(default_factory=ModuleResultConfig)
    medication: MedicationTrackerConfig = field(default_factory=MedicationTrackerConfig)
    revereTest: RevereTestConfig = field(default_factory=RevereTestConfig)
    twilioVideo: TwilioVideoConfig = field(default_factory=TwilioVideoConfig)
    kardia: KardiaConfig = field(default_factory=KardiaConfig)
    exportDeployment: ExportDeploymentConfig = field(
        default_factory=ExportDeploymentConfig
    )
    publisher: PublisherConfig = field(default_factory=PublisherConfig)
    invitation: InvitationConfig = field(default_factory=InvitationConfig)
    adapters: ExtensionAdapters = required_field()
    identityVerification: IdentityVerificationConfig = field(
        default_factory=IdentityVerificationConfig
    )


@convertibleclass
class ExtensionServerConfig(PhoenixServerConfig):
    server: ExtensionServer = required_field()
