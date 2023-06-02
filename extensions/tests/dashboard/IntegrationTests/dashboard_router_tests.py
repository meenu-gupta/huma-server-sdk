from pathlib import Path

from freezegun import freeze_time

from extensions.authorization.component import AuthorizationComponent
from extensions.dashboard.component import DashboardComponent
from extensions.dashboard.models.dashboard import (
    Dashboard,
    DashboardId,
)
from extensions.dashboard.models.gadget import GadgetId, GadgetLink
from extensions.dashboard.models.gadgets import (
    SignedUpGadget,
    ConsentedGadget,
    KeyMetricsGadget,
    OverallViewGadget,
)
from extensions.dashboard.router.dashboard_requests import (
    RetrieveGadgetDataRequestObject,
)
from extensions.deployment.component import DeploymentComponent
from extensions.module_result.component import ModuleResultComponent
from extensions.organization.component import OrganizationComponent
from extensions.tests.test_case import ExtensionTestCase
from sdk.auth.component import AuthComponent
from sdk.common.utils.common_functions_utils import round_half_up
from tools.mongodb_script.gadget_populate_data import upload_test_gadgets_data

VALID_SUPER_ADMIN_ID = "5e8f0c74b50aa9656c34789c"
VALID_ORGANIZATION_STAFF_ID = "5e8f0c74b50aa9656c34789a"
USER_ID_WITHOUT_PERMISSIONS = "5e84b0dab8dfa268b1180536"
ACCESS_CONTROLLER_ID = "5ed803dd5f2f99da73654410"
ACCESS_CONTROLLER_NO_USERS_ORG = "5ed803dd5f2f99da73654411"
ORGANIZATION_ID = "5fde855f12db509a2785da06"
ORGANIZATION_WITHOUT_DASHBOARD = "6283ae450cfb61eddf91cfc8"
ORG_ID_FOR_SCRIPT = "629e31327f9aecc7760b2f45"
ACCESS_CONTROLLER_ID_FOR_SCRIPT_ORG = "5ed803dd5f2f99da73654413"
DASHBOARD_ID = DashboardId.ORGANIZATION_OVERVIEW.value
CONSENTED_GADGET_ID = GadgetId.CONSENTED.value
SIGNED_UP_GADGET_ID = GadgetId.SIGNED_UP.value
KEY_METRICS_GADGET_ID = GadgetId.KEY_METRICS.value
OVERALL_VIEW_GADGET_ID = GadgetId.OVERALL_VIEW.value


# Deployment Y
DEPLOYMENT_Y_ID = "625d3c4958679c8c4c811445"
VALID_ADMIN_Y = "625d3b1858679c8c4c811442"
DEPLOYMENT_STAFF = "62430e8dc0f81ef8563ba6eb"
CONTRIBUTOR = "62430e8dc0f81ef8573ba6eb"


class BaseDashboardRouterTestCase(ExtensionTestCase):
    components = [
        AuthComponent(),
        AuthorizationComponent(),
        DeploymentComponent(),
        OrganizationComponent(),
        DashboardComponent(),
        ModuleResultComponent(),
    ]

    fixtures = [Path(__file__).parent.joinpath("fixtures/dashboard_dump.json")]
    dashboards_route = "/api/extensions/v1beta/dashboards"
    org_dash_url = f"{dashboards_route}/organization/{ORGANIZATION_ID}"
    deployment_dash_url = f"{dashboards_route}/deployment/{DEPLOYMENT_Y_ID}"
    organization_dashboard_route = f"{org_dash_url}/dashboard/{DASHBOARD_ID}"
    deployment_dashboard_route = f"{deployment_dash_url}/dashboard/{DASHBOARD_ID}"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.test_server.config.server.debugRouter = False
        self.headers = self.get_headers_for_token(ACCESS_CONTROLLER_ID)
        self.admin_headers = self.get_headers_for_token(VALID_ADMIN_Y)


class OrganizationDashboardRouterTestCase(BaseDashboardRouterTestCase):
    def test_success_retrieve_dashboards(self):
        rsp = self.flask_client.get(
            self.org_dash_url,
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self._validate_dashboard_gadgets_response(rsp.json[0])

    def test_success_retrieve_dashboard(self):
        rsp = self.flask_client.get(
            f"{self.organization_dashboard_route}",
            headers=self.headers,
        )
        self.assertEqual(200, rsp.status_code)
        self._validate_dashboard_gadgets_response(rsp.json)

    def test_success_retrieve_dashboard__org_staff(self):
        rsp = self.flask_client.get(
            f"{self.organization_dashboard_route}",
            headers=self.get_headers_for_token(VALID_ORGANIZATION_STAFF_ID),
        )
        self.assertEqual(200, rsp.status_code)
        self._validate_dashboard_gadgets_response(rsp.json)

    def test_failure_view_dashboard__no_permissions(self):
        rsp = self.flask_client.get(
            f"{self.organization_dashboard_route}",
            headers=self.get_headers_for_token(USER_ID_WITHOUT_PERMISSIONS),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_view_dashboard__super_admin_permissions(self):
        rsp = self.flask_client.get(
            f"{self.organization_dashboard_route}",
            headers=self.get_headers_for_token(VALID_SUPER_ADMIN_ID),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_view_dashboard__different_org(self):
        rsp = self.flask_client.get(
            f"{self.organization_dashboard_route}",
            headers=self.get_headers_for_token(ACCESS_CONTROLLER_ID_FOR_SCRIPT_ORG),
        )
        self.assertEqual(403, rsp.status_code)

    def test_failure_view_dashboard__not_org_deployment_ids(self):
        data = {
            RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: ["629e30cdf3dcc4921092c7e8"]
        }
        rsp = self.flask_client.post(
            f"{self.org_dash_url}/gadget/{CONSENTED_GADGET_ID}/data",
            headers=self.headers,
            json=data,
        )
        self.assertEqual(403, rsp.status_code)

    @freeze_time("2022-06-30")
    def test_success_retrieve_consented_gadget_data__en(self):
        _, depl_ids = upload_test_gadgets_data(
            self.mongo_database, self.mongo_client, ORG_ID_FOR_SCRIPT
        )
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_ID_FOR_SCRIPT_ORG)
        data = {RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: depl_ids}
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORG_ID_FOR_SCRIPT}/gadget/{CONSENTED_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        gadget_data = rsp.json
        self.assertEqual(74, gadget_data[ConsentedGadget.AVG])
        self.assertEqual(39, len(gadget_data[ConsentedGadget.DATA]))

        field_names_with_expected_values = {
            ConsentedGadget.TITLE: "Consented",
            ConsentedGadget.TOOLTIP: "Figures shown are calculated from first patient in across all the selected sites.",
            ConsentedGadget.METADATA: {
                "chart": {"avg": {"tooltip": "Avg. monthly consented"}}
            },
            ConsentedGadget.INFO_FIELDS: [
                {"name": "Monthly target", "value": "<strong>63</strong>"},
                {"name": "Avg. monthly consented", "value": "<strong>74</strong>"},
                {
                    "name": "Expected consented completion",
                    "value": "<strong>2022-05-01</strong>",
                },
            ],
            ConsentedGadget.ID: GadgetId.CONSENTED.value,
        }
        for field_name, expected_value in field_names_with_expected_values.items():
            self.assertEqual(expected_value, rsp.json[field_name])

    def test_success_retrieve_consented_gadget_data_without_consented_users(self):
        data = {
            RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: ["629e30cdf3dcc4921092c7f8"]
        }
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORGANIZATION_ID}/gadget/{CONSENTED_GADGET_ID}/data",
            headers=self.headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(0, len(rsp.json["data"]))
        info_fields = rsp.json.get("infoFields")
        self.assertEqual(3, len(info_fields))
        self.assertIsNotNone(info_fields)
        self.assertEqual(None, info_fields[0]["value"])
        self.assertIsNone(info_fields[1]["value"])
        self.assertEqual(None, info_fields[2]["value"])

    def test_success_retrieve_signed_gadget_data__en(self):
        deployment_ids = ["629e30cdf3dcc4921092c7f8", "5fde855f12db509a2785d899"]
        data = {RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: deployment_ids}
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORGANIZATION_ID}/gadget/{SIGNED_UP_GADGET_ID}/data",
            headers=self.headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, rsp.json["data"][0]["y"])
        field_names_with_expected_values = {
            SignedUpGadget.TITLE: "Signed up",
            SignedUpGadget.TOOLTIP: "Figures shown are calculated from first patient in across all the selected sites.",
            SignedUpGadget.METADATA: {
                "chart": {"avg": {"tooltip": "Avg. monthly signed up"}}
            },
            SignedUpGadget.INFO_FIELDS: [
                {"name": "Avg. monthly signed up", "value": "<strong>1</strong>"}
            ],
            SignedUpGadget.ID: GadgetId.SIGNED_UP.value,
        }
        for field_name, expected_value in field_names_with_expected_values.items():
            self.assertEqual(expected_value, rsp.json[field_name])

        self._validate_averages_calculation(rsp.json, deployment_ids)

        # check that empty data also persist
        for data in rsp.json["data"][2:]:
            self.assertEqual(0, data["y"])

    def test_retrieve_signed_up_data_no_users_in_deployment(self):
        data = {
            RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: ["629e30cdf3dcc4921092c7e8"]
        }
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_NO_USERS_ORG)
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/629e31327f9aecc7760b2f40/gadget/{SIGNED_UP_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)

    def test_retrieve_key_metrics__en(self):
        _, depl_ids = upload_test_gadgets_data(
            self.mongo_database, self.mongo_client, ORG_ID_FOR_SCRIPT
        )
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_ID_FOR_SCRIPT_ORG)
        data = {RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: depl_ids}
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORG_ID_FOR_SCRIPT}/gadget/{KEY_METRICS_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(6, len(rsp.json[KeyMetricsGadget.DATA]))

        field_names_with_expected_values = {
            KeyMetricsGadget.TITLE: "Key metric",
            KeyMetricsGadget.TOOLTIP: "Consented shows the number of patients who consented against the target consented across all selected sites. Completed shows the number of patients that completed their last study task/form against the target completed across all selected sites.",
            KeyMetricsGadget.METADATA: {
                "chart": {
                    "Completed": {"max": 500, "min": 0},
                    "Consented": {"max": 1050, "min": 0},
                    "bars": ["Consented", "Completed"],
                }
            },
            KeyMetricsGadget.INFO_FIELDS: [
                {"name": "Consented", "value": "<strong>964</strong>/1050"},
                {"name": "Completed", "value": "<strong>354</strong>/500"},
            ],
            KeyMetricsGadget.ID: GadgetId.KEY_METRICS.value,
        }
        for field_name, expected_value in field_names_with_expected_values.items():
            self.assertEqual(expected_value, rsp.json[field_name])

    def test_retrieve_overall_gadget_no_data_exist(self):
        data = {
            RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: ["629e30cdf3dcc4921092c7e8"]
        }
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_NO_USERS_ORG)
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/629e31327f9aecc7760b2f40/gadget/{OVERALL_VIEW_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)

    def test_retrieve_overall_view_gadget__en(self):
        _, depl_ids = upload_test_gadgets_data(
            self.mongo_database, self.mongo_client, ORG_ID_FOR_SCRIPT
        )
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_ID_FOR_SCRIPT_ORG)
        data = {RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: depl_ids}
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORG_ID_FOR_SCRIPT}/gadget/{OVERALL_VIEW_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        field_names_with_expected_values = {
            OverallViewGadget.DATA: [
                {"x": "Signed up", "y": 100, "y2": 1500, "y3": 0, "y4": 0},
                {
                    "x": "ID verified",
                    "y": "80.3%",
                    "y2": 1205,
                    "y3": "14.5%",
                    "y4": 217,
                },
                {
                    "x": "Consented",
                    "y": "64.3%",
                    "y2": 964,
                    "y3": "12.6%",
                    "y4": 189,
                },
                {"x": "Completed", "y": "23.6%", "y2": 354, "y3": "15.9%", "y4": 239},
            ],
            OverallViewGadget.TITLE: "Overall view",
            OverallViewGadget.TOOLTIP: "Shows the dropped-off of patients during recruitment from first patient in till present day across all the selected sites.",
            OverallViewGadget.METADATA: {
                "chart": {
                    "tooltip": {
                        "Completed": [
                            {"header": True, "name": "Completed", "value": "23.6%"},
                            {"name": "Have not completed study", "value": "24.7%"},
                            {"name": "Withdrew consent", "value": "7.9%"},
                            {"name": "Manual off-boarded", "value": "8.1%"},
                        ],
                        "Consented": [
                            {"header": True, "name": "Consented", "value": "64.3%"},
                            {"name": "Refused consent", "value": "12.6%"},
                            {"name": "Have not consented", "value": "3.5%"},
                        ],
                        "ID verified": [
                            {"header": True, "name": "ID verified", "value": "80.3%"},
                            {"name": "Failed ID verification", "value": "14.5%"},
                            {
                                "name": "Have not completed ID verification",
                                "value": "5.2%",
                            },
                        ],
                        "Signed up": [
                            {
                                "header": True,
                                "name": "Completed sign-up",
                                "value": "100%",
                            }
                        ],
                    },
                    "x": {
                        "bars": ["Signed up", "ID verified", "Consented", "Completed"]
                    },
                    "y": {"max": 100, "min": 0},
                }
            },
            OverallViewGadget.INFO_FIELDS: [
                {"name": "Total participants", "value": "<strong>1500</strong>"},
                {"name": "Current drop off rate", "value": "<strong>43%</strong>"},
                {
                    "name": "Largest drop off",
                    "value": "<strong> Between Consented and Completed </strong>",
                },
            ],
            OverallViewGadget.ID: GadgetId.OVERALL_VIEW.value,
        }
        for field_name, expected_value in field_names_with_expected_values.items():
            self.assertEqual(expected_value, rsp.json[field_name])

    def test_overall_view_gadget__modules_that_should_not_be_counted(self):
        data = {
            RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: [
                "5fde855f12db509a2785d899",
                "629e30cdf3dcc4921092c7f8",
            ]
        }
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/5fde855f12db509a2785da06/gadget/{OVERALL_VIEW_GADGET_ID}/data",
            headers=self.headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(3, len(rsp.json[OverallViewGadget.DATA]))

    def test_retrieve_key_metrics__send_request_a_few_times(self):
        _, depl_ids = upload_test_gadgets_data(
            self.mongo_database, self.mongo_client, ORG_ID_FOR_SCRIPT
        )
        headers = self.get_headers_for_token(ACCESS_CONTROLLER_ID_FOR_SCRIPT_ORG)
        data = {RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: depl_ids[2:]}
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORG_ID_FOR_SCRIPT}/gadget/{KEY_METRICS_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json[KeyMetricsGadget.DATA]))

        data = {RetrieveGadgetDataRequestObject.DEPLOYMENT_IDS: depl_ids[:1]}
        rsp = self.flask_client.post(
            f"{self.dashboards_route}/organization/{ORG_ID_FOR_SCRIPT}/gadget/{KEY_METRICS_GADGET_ID}/data",
            headers=headers,
            json=data,
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(2, len(rsp.json[KeyMetricsGadget.DATA]))

    def _validate_averages_calculation(self, json_res, deployment_ids):
        num_of_months = len(json_res["data"]) / len(deployment_ids)
        total_signups = 0
        for rec in json_res["data"]:
            total_signups += rec["y"]
        avg_sign_up_by_month = round_half_up(total_signups / num_of_months)
        self.assertEqual(avg_sign_up_by_month, json_res[SignedUpGadget.AVG])

    @staticmethod
    def _sample_dashboard():
        return {
            Dashboard.GADGETS: [
                {
                    GadgetLink.SIZE: "2x2",
                    GadgetLink.ORDER: 1,
                    GadgetLink.ID: GadgetId.SIGNED_UP.value,
                },
                {
                    GadgetLink.SIZE: "2x2",
                    GadgetLink.ORDER: 2,
                    GadgetLink.ID: GadgetId.CONSENTED.value,
                },
                {
                    GadgetLink.SIZE: "2x2",
                    GadgetLink.ORDER: 3,
                    GadgetLink.ID: GadgetId.KEY_METRICS.value,
                },
                {
                    GadgetLink.SIZE: "2x2",
                    GadgetLink.ORDER: 4,
                    GadgetLink.ID: GadgetId.OVERALL_VIEW.value,
                },
            ],
            Dashboard.ID: DASHBOARD_ID,
            Dashboard.NAME: "Overview of ABC Pharmaceuticals EU Trials 123",
        }

    def _validate_dashboard_gadgets_response(self, res):
        for key in self._sample_dashboard()[Dashboard.GADGETS]:
            self.assertIn(key, res[Dashboard.GADGETS])
