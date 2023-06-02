from enum import Enum


class SummaryReportAction(Enum):
    CreateSummaryReport = "CreateSummaryReport"
    RunAsyncSummaryReport = "RunAsyncSummaryReport"


class ExportDataAction(Enum):
    ExportPatientsListData = "ExportPatientsListData"
