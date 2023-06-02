from aenum import Enum, NoAlias


class LocalizableEnum(Enum):
    _init_ = "value key"
    _settings_ = NoAlias

    def __int__(self):
        return self.value


class DashboardLocalizationKeys(Enum):
    TITLE = "Dashboard.OrganizationOverview.title"


class SignedUpGadgetLocalizationKeys(LocalizableEnum):
    TITLE = "TITLE", "Common.SignedUp"
    TOOLTIP = "TOOLTIP", "Gadget.SignedUp.tooltip"
    INFO_AVG_MONTHLY = "INFO_AVG_MONTHLY", "Common.AvgMonthlySignedUp"
    CHART_TOOLTIP = "CHART_TOOLTIP", "Common.AvgMonthlySignedUp"


class ConsentedGadgetLocalizationKeys(LocalizableEnum):
    TITLE = "TITLE", "Common.Consented"
    TOOLTIP = "TOOLTIP", "Gadget.Consented.tooltip"
    INFO_MONTHLY_TARGET = "INFO_MONTHLY_TARGET", "Common.MonthlyTarget"
    INFO_AVG_MONTHLY = "INFO_AVG_MONTHLY", "Common.AvgMonthlyConsented"
    INFO_EXP_ENROLLMENT = "INFO_EXP_ENROLLMENT", "Common.ExpectedEnrollmentCompletion"
    TOOLTIP_AVG_MONTHLY = "TOOLTIP_AVG_MONTHLY", "Common.AvgMonthlyConsented"


class KeyMetricsGadgetLocalization(LocalizableEnum):
    TITLE = "TITLE", "Common.KeyMetrics"
    TOOLTIP_CONSENTED = "TOOLTIP_CONSENTED", "Gadget.KeyMetrics.consentedTooltip"
    TOOLTIP_COMPLETED = "TOOLTIP_COMPLETED", "Gadget.KeyMetrics.completedTooltip"
    CONSENTED = "CONSENTED", "Common.Consented"
    COMPLETED = "COMPLETED", "Common.Completed"


class OverallViewGadgetLocalization(LocalizableEnum):
    TITLE = "TITLE", "Common.OverallView"
    TOOLTIP = "TOOLTIP", "Gadget.OverallView.tooltip"
    AND = "AND", "Common.And"
    BETWEEN = "BETWEEN", "Common.Between"
    CURRENT_DROP_OFF = "CURRENT_DROP_OFF", "Common.CurrentDropOffRate"
    LARGEST_DROP_OFF = "LARGEST_DROP_OFF", "Common.LargestDropOff"
    TOTAL_PARTICIPANTS = "TOTAL_PARTICIPANTS", "Common.TotalParticipants"
    ID_VERIFIED = "ID_VERIFIED", "Common.IDVerified"
    PRE_SCREENED = "PRE_SCREENED", "Common.PreScreened"
    COMPLETED = "COMPLETED", "Common.Completed"
    SIGNED_UP = "SIGNED_UP", "Common.SignedUp"
    CONSENTED = "CONSENTED", "Common.Consented"
    TOOLTIP_PASSED_ID_VERIFICATION = (
        "TOOLTIP_PASSED_ID_VERIFICATION",
        "Common.PassedIDVerification",
    )
    TOOLTIP_COMPLETED_SIGN_UP = "TOOLTIP_COMPLETED_SIGN_UP", "Common.CompletedSignUp"
    TOOLTIP_COMPLETED_STUDY = "TOOLTIP_COMPLETED_STUDY", "Common.CompletedStudy"
    TOOLTIP_HAVE_NOT_COMPLETED_STUDY = (
        "TOOLTIP_HAVE_NOT_COMPLETED_STUDY",
        "Common.HaveNotCompletedStudy",
    )
    TOOLTIP_HAVE_NOT_CONSENTED = "TOOLTIP_HAVE_NOT_CONSENTED", "Common.HaveNotConsented"
    TOOLTIP_MANUAL_OFF_BOARDED = "TOOLTIP_MANUAL_OFF_BOARDED", "Common.ManualOffBoarded"
    TOOLTIP_NOT_COMPLETED_PRE_SCREENING = (
        "TOOLTIP_NOT_COMPLETED_PRE_SCREENING",
        "Common.HaveNotCompletedPreScreening",
    )
    TOOLTIP_PASSED_PRE_SCREENING = (
        "TOOLTIP_PASSED_PRE_SCREENING",
        "Common.PassedPreScreening",
    )
    TOOLTIP_REFUSED_CONSENT = "TOOLTIP_REFUSED_CONSENT", "Common.RefusedConsent"
    TOOLTIP_WITHDREW_CONSENT = "TOOLTIP_WITHDREW_CONSENT", "Common.WithdrewConsent"
    TOOLTIP_FAILED_PRE_SCREENING = (
        "TOOLTIP_FAILED_PRE_SCREENING",
        "Common.FailedPreScreening",
    )
    TOOLTIP_NOT_REQUIRE_PRE_SCREENING = (
        "TOOLTIP_NOT_REQUIRE_PRE_SCREENING",
        "Common.DoNotRequirePreScreening",
    )
    TOOLTIP_NOT_REQUIRE_ID_VERIFICATION = (
        "TOOLTIP_NOT_REQUIRE_ID_VERIFICATION",
        "Common.DoNotRequireIDVerification",
    )
    TOOLTIP_NOT_REQUIRE_CONSENT = (
        "TOOLTIP_NOT_REQUIRE_CONSENT",
        "Common.DoNotRequireConsent",
    )
    TOOLTIP_NOT_COMPLETED_ID_VERIFICATION = (
        "TOOLTIP_NOT_COMPLETED_ID_VERIFICATION",
        "Common.NotCompletedIDVerification",
    )
    TOOLTIP_FAILED_ID_VERIFICATION = (
        "TOOLTIP_FAILED_ID_VERIFICATION",
        "Common.FailedIDVerification",
    )
    DIFFERENT_CONFIGS = (
        "DIFFERENT_CONFIGS",
        "Gadget.OverallView.onboardingDifferencesMessage",
    )
