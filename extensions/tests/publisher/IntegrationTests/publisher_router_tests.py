from pathlib import Path

from extensions.authorization.component import AuthorizationComponent
from extensions.deployment.component import DeploymentComponent
from extensions.export_deployment.component import ExportDeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.publisher.component import PublisherComponent
from extensions.publisher.models.publisher import Publisher
from extensions.publisher.models.webhook import Webhook
from extensions.publisher.models.gcp_fhir import GCPFhir
from extensions.revere.component import RevereComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.calendar.component import CalendarComponent
from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values
from sdk.versioning.component import VersionComponent


class PublisherRouterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        PublisherComponent(),
        ExportDeploymentComponent(),
        CalendarComponent(),
        RevereComponent(),
        OrganizationComponent(),
        ModuleResultComponent(),
        VersionComponent(server_version="1.0.0", api_version="1.0.0"),
    ]

    VALID_USER_ID = "615db4dd92a28f0cee2e14c1"

    COMMON_API_URL = f"/api/extensions/v1beta/publisher"
    CREATE_API_URL = (
        f"api/extensions/v1beta/user/{VALID_USER_ID}/module-result/BloodPressure"
    )

    fixtures = [Path(__file__).parent.joinpath("fixtures/data.json")]

    migration_path: str = str(Path(__file__).parent.parent.parent) + "/migrations"

    def setUp(self):
        super().setUp()

        jwt_adapter = inject.instance(TokenAdapter)
        ref_token = jwt_adapter.create_access_token(identity=self.VALID_USER_ID)
        self.headers = {"Authorization": f"Bearer {ref_token}"}

    @staticmethod
    def get_sample_request_data(
        name: str = None,
        organization_ids: list[str] = None,
        deployment_ids: list[str] = None,
        publisher_type: str = Publisher.Target.Type.WEBHOOK.value,
        event_type: str = Publisher.Filter.EventType.MODULE_RESULT.value,
        listener_type: str = Publisher.Filter.ListenerType.DEPLOYMENT_IDS.value,
        deidentified: bool = None,
        webhook: Webhook = None,
        gcpfhir: GCPFhir = None,
    ):
        request_data = {
            Publisher.PUBLISHER_NAME: name,
            Publisher.PUBLISHER_TRANSFORM: {
                Publisher.INCLUDE_USER_META_DATA: False,
                Publisher.INCLUDE_NULL_FIELDS: False,
                Publisher.DEIDENTIFIED: deidentified,
            },
            Publisher.PUBLISHER_TARGET: {
                Publisher.PUBLISHER_TYPE: publisher_type,
            },
            Publisher.PUBLISHER_FILTER: {
                Publisher.DEPLOYMENT_IDS: deployment_ids,
                Publisher.ORGANIZATION_IDS: organization_ids,
                Publisher.EVENT_TYPE: event_type,
                Publisher.LISTENER_TYPE: listener_type,
            },
        }

        if publisher_type == Publisher.Target.Type.GCPFHIR.value:
            request_data[Publisher.PUBLISHER_TARGET][Publisher.GCPFHIR] = gcpfhir
        elif publisher_type == Publisher.Target.Type.WEBHOOK.value:
            request_data[Publisher.PUBLISHER_TARGET][Publisher.WEBHOOK] = webhook

        return remove_none_values(request_data)
