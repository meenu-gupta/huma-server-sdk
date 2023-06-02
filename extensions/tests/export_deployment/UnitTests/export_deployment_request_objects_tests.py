from datetime import datetime, timedelta
from unittest import TestCase

import pytz
from bson import ObjectId
from dateutil.relativedelta import relativedelta

from extensions.appointment.exceptions import InvalidDateException
from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import Deployment
from extensions.export_deployment.use_case.export_request_objects import (
    RetrieveExportDeploymentProcessesRequestObject,
    CheckExportDeploymentTaskStatusRequestObject,
    RunExportTaskRequestObject,
    ExportRequestObject,
)
from extensions.export_deployment.use_case.summary_report_request_objects import (
    GenerateSummaryReportRequestObject,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import utc_str_field_to_val

SAMPLE_DEPLOYMENT_ID = "5fe0b3bb2896c6d525461086"


class TestRetrieveExportDeploymentProcessesRequestObject(TestCase):
    def test_failure_no_deployment_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RetrieveExportDeploymentProcessesRequestObject.from_dict({})

    def test_success_export_deployment_processes_request_object(self):
        request_object = RetrieveExportDeploymentProcessesRequestObject.from_dict(
            {"deploymentId": SAMPLE_DEPLOYMENT_ID}
        )
        self.assertIsNotNone(request_object)


class TestCheckExportDeploymentTaskStatusRequestObject(TestCase):
    def test_failure_no_process_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CheckExportDeploymentTaskStatusRequestObject.from_dict(
                {
                    "deploymentId": SAMPLE_DEPLOYMENT_ID,
                }
            )

    def test_failure_no_deployment_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            CheckExportDeploymentTaskStatusRequestObject.from_dict(
                {
                    "exportProcessId": "5fe0b52b24f10259fa13bf1b",
                }
            )

    def test_success_creation_request_object(self):
        request_object = CheckExportDeploymentTaskStatusRequestObject.from_dict(
            {
                "exportProcessId": "5fe0b52b24f10259fa13bf1b",
                "deploymentId": SAMPLE_DEPLOYMENT_ID,
            }
        )
        self.assertIsNotNone(request_object)


class TestRunExportDeploymentTaskRequestObject(TestCase):
    def test_failure_no_deployment_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RunExportTaskRequestObject.from_dict(
                {
                    "requesterId": "5fe0b5c445f819b3f43537c3",
                }
            )

    def test_failure_no_requester_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            RunExportTaskRequestObject.from_dict(
                {
                    "deploymentId": SAMPLE_DEPLOYMENT_ID,
                }
            )

    def test_success_creation_request_object(self):
        request_object = RunExportTaskRequestObject.from_dict(
            {
                "requesterId": "5fe0b5c445f819b3f43537c3",
                "deploymentId": SAMPLE_DEPLOYMENT_ID,
            }
        )
        self.assertIsNotNone(request_object)


class TestExportDeploymentRequestObject(TestCase):
    def test_failure_without_deployment_id(self):
        with self.assertRaises(ConvertibleClassValidationError):
            ExportRequestObject.from_dict({})

    def test_success_creation_request_object(self):
        request_object = ExportRequestObject.from_dict(
            {"deploymentId": SAMPLE_DEPLOYMENT_ID}
        )
        self.assertIsNotNone(request_object)

    def test_date_range_conversion_from_date_logic_valid(self):
        sample_from_date = datetime(
            day=1, month=5, year=2020, hour=0, minute=0, tzinfo=pytz.timezone("UTC")
        )
        sample_to_date = datetime(
            day=1,
            month=5,
            year=2020,
            hour=23,
            minute=59,
            second=59,
            microsecond=999,
            tzinfo=pytz.timezone("UTC"),
        )

        # testing date string
        data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.FROM_DATE: "2020-05-01",
            ExportRequestObject.TO_DATE: "2020-05-01",
        }
        request_object = ExportRequestObject.from_dict(data)
        self.assertEqual(sample_from_date, request_object.fromDate)
        self.assertEqual(sample_to_date, request_object.toDate)

        # testing date object
        data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.FROM_DATE: sample_to_date.date(),
            ExportRequestObject.TO_DATE: sample_from_date.date(),
        }
        request_object = ExportRequestObject.from_dict(data)
        self.assertEqual(sample_from_date, request_object.fromDate)
        self.assertEqual(sample_to_date, request_object.toDate)

    def test_date_range_conversion_from_datetime_logic_valid(self):
        sample_from_datetime = datetime(
            day=1, month=5, year=2020, hour=8, minute=15, tzinfo=pytz.timezone("UTC")
        )
        sample_to_datetime = datetime(
            day=1, month=5, year=2020, hour=8, minute=16, tzinfo=pytz.timezone("UTC")
        )

        # from datetime string
        data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.FROM_DATE: "2020-05-01T08:15:00Z",
            ExportRequestObject.TO_DATE: "2020-05-01T08:16:00Z",
        }
        request_object = ExportRequestObject.from_dict(data)
        self.assertEqual(sample_from_datetime, request_object.fromDate)
        self.assertEqual(sample_to_datetime, request_object.toDate)

        # from datetime object
        data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.FROM_DATE: sample_from_datetime,
            ExportRequestObject.TO_DATE: sample_to_datetime,
        }
        request_object = ExportRequestObject.from_dict(data)
        self.assertEqual(sample_from_datetime, request_object.fromDate)
        self.assertEqual(sample_to_datetime, request_object.toDate)

        # from datetime string with changed timezone
        data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.FROM_DATE: "2020-05-01T11:15:00+03:00",
            ExportRequestObject.TO_DATE: "2020-05-01T11:16:00+03:00",
        }
        request_object = ExportRequestObject.from_dict(data)
        self.assertEqual(sample_from_datetime, request_object.fromDate)
        self.assertEqual(sample_to_datetime, request_object.toDate)

    def test_user_ids_validation(self):
        data = {
            ExportRequestObject.DEPLOYMENT_ID: SAMPLE_DEPLOYMENT_ID,
            ExportRequestObject.USER_IDS: ["invalid"],
        }
        with self.assertRaises(ConvertibleClassValidationError):
            ExportRequestObject.from_dict(data)

        user_ids = [str(ObjectId())]
        data[ExportRequestObject.USER_IDS] = user_ids
        request_object = ExportRequestObject.from_dict(data)
        self.assertEqual(user_ids, request_object.userIds)

    def test_failure_summary_report_request_object(self):
        with self.assertRaises(InvalidDateException) as context:
            GenerateSummaryReportRequestObject.from_dict(
                {
                    GenerateSummaryReportRequestObject.USER: User(
                        id=SAMPLE_DEPLOYMENT_ID
                    ),
                    GenerateSummaryReportRequestObject.DEPLOYMENT: Deployment(
                        id=SAMPLE_DEPLOYMENT_ID
                    ),
                    GenerateSummaryReportRequestObject.REQUESTER_ID: SAMPLE_DEPLOYMENT_ID,
                    GenerateSummaryReportRequestObject.START_DATE_TIME: "2022-05-05T06:55:56.650Z",
                    GenerateSummaryReportRequestObject.END_DATE_TIME: "2022-04-30T06:55:56.653Z",
                    GenerateSummaryReportRequestObject.FORMAT: "PDF",
                }
            )
        self.assertEqual(
            str(context.exception), "Start date time can't be later than end."
        )

    def test_failure_summary_report_request_object_with_no_end_date_time(self):
        with self.assertRaises(InvalidDateException) as context:
            GenerateSummaryReportRequestObject.from_dict(
                {
                    GenerateSummaryReportRequestObject.USER: User(
                        id=SAMPLE_DEPLOYMENT_ID
                    ),
                    GenerateSummaryReportRequestObject.DEPLOYMENT: Deployment(
                        id=SAMPLE_DEPLOYMENT_ID
                    ),
                    GenerateSummaryReportRequestObject.REQUESTER_ID: SAMPLE_DEPLOYMENT_ID,
                    GenerateSummaryReportRequestObject.START_DATE_TIME: utc_str_field_to_val(
                        datetime.utcnow() + timedelta(hours=1)
                    ),
                    GenerateSummaryReportRequestObject.FORMAT: "PDF",
                }
            )
        self.assertEqual(
            str(context.exception), "Start date time can't be later than end."
        )

    def test_failure_summary_report_request_object_with_no_start_date_time(self):
        with self.assertRaises(InvalidDateException) as context:
            GenerateSummaryReportRequestObject.from_dict(
                {
                    GenerateSummaryReportRequestObject.USER: User(
                        id=SAMPLE_DEPLOYMENT_ID
                    ),
                    GenerateSummaryReportRequestObject.DEPLOYMENT: Deployment(
                        id=SAMPLE_DEPLOYMENT_ID
                    ),
                    GenerateSummaryReportRequestObject.REQUESTER_ID: SAMPLE_DEPLOYMENT_ID,
                    GenerateSummaryReportRequestObject.END_DATE_TIME: utc_str_field_to_val(
                        datetime.utcnow() - relativedelta(months=7)
                    ),
                    GenerateSummaryReportRequestObject.FORMAT: "PDF",
                }
            )
        self.assertEqual(
            str(context.exception), "Start date time can't be later than end."
        )
