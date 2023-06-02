import logging
from dataclasses import field, dataclass
from datetime import datetime
from enum import Enum

import i18n
from dateutil import rrule

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.services.authorization import AuthorizationService
from extensions.deployment.service.deployment_service import DeploymentService
from extensions.module_result.models.module_config import NotificationData
from sdk.calendar.models.calendar_event import CalendarEvent
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.utils.common_functions_utils import deprecated
from sdk.common.utils.convertible import default_field, meta, required_field
from sdk.common.utils.date_utils import get_time_from_duration_iso
from sdk.common.utils.validators import (
    not_empty,
    validate_min_max_month_days_list,
    validate_time_duration,
    remove_none_values,
    remove_duplicates,
    utc_str_val_to_field,
    utc_str_field_to_val,
)

logger = logging.getLogger(__name__)


@deprecated("Use `moduleConfig.notificationData` instead.")
def get_reminder_notification_templates(locale: str) -> dict:
    """@deprecated"""
    return {
        "BloodGlucose": {
            "title": i18n.t("Reminder.BloodGlucose.title", locale=locale),
            "body": i18n.t("Reminder.BloodGlucose.body", locale=locale),
        },
        "PostVaccination": {
            "title": i18n.t("Reminder.PostVaccination.title", locale=locale),
            "body": i18n.t("Reminder.PostVaccination.body", locale=locale),
        },
        "BloodPressure": {
            "title": i18n.t("Reminder.BloodPressure.title", locale=locale),
            "body": i18n.t("Reminder.BloodPressure.body", locale=locale),
        },
        "HeartRate": {
            "title": i18n.t("Reminder.HeartRate.title", locale=locale),
            "body": i18n.t("Reminder.HeartRate.body", locale=locale),
        },
        "MedicationTracker": {
            "title": i18n.t("Reminder.MedicationTracker.title", locale=locale),
            "body": i18n.t("Reminder.MedicationTracker.body", locale=locale),
        },
        "Journal": {
            "title": i18n.t("Reminder.Journal.title", locale=locale),
            "body": i18n.t("Reminder.Journal.body", locale=locale),
        },
        "Photo": {
            "title": i18n.t("Reminder.Photo.title", locale=locale),
            "body": i18n.t("Reminder.Photo.body", locale=locale),
        },
        "PulseOximetry": {
            "title": i18n.t("Reminder.PulseOximetry.title", locale=locale),
            "body": i18n.t("Reminder.PulseOximetry.body", locale=locale),
        },
        "Questionnaire": {
            "title": i18n.t("Reminder.Questionnaire.title", locale=locale),
            "body": i18n.t("Reminder.Questionnaire.body", locale=locale),
        },
        "Spirometry": {
            "title": i18n.t("Reminder.Spirometry.title", locale=locale),
            "body": i18n.t("Reminder.Spirometry.body", locale=locale),
        },
        "Symptom": {
            "title": i18n.t("Reminder.Symptom.title", locale=locale),
            "body": i18n.t("Reminder.Symptom.body", locale=locale),
        },
        "Temperature": {
            "title": i18n.t("Reminder.Temperature.title", locale=locale),
            "body": i18n.t("Reminder.Temperature.body", locale=locale),
        },
        "TimedUpAndGo": {
            "title": i18n.t("Reminder.TimedUpAndGo.title", locale=locale),
            "body": i18n.t("Reminder.TimedUpAndGo.body", locale=locale),
        },
        "Video": {
            "title": i18n.t("Reminder.Video.title", locale=locale),
            "body": i18n.t("Reminder.Video.body", locale=locale),
        },
        "Weight": {
            "title": i18n.t("Reminder.Weight.title", locale=locale),
            "body": i18n.t("Reminder.Weight.body", locale=locale),
        },
        "WoundAnalyser": {
            "title": i18n.t("Reminder.WoundAnalyser.title", locale=locale),
            "body": i18n.t("Reminder.WoundAnalyser.body", locale=locale),
        },
        "RestingHeartRate": {
            "title": i18n.t("Reminder.RestingHeartRate.title", locale=locale),
            "body": i18n.t("Reminder.RestingHeartRate.body", locale=locale),
        },
        "Breathlessness": {
            "title": i18n.t("Reminder.Breathlessness.title", locale=locale),
            "body": i18n.t("Reminder.Breathlessness.body", locale=locale),
        },
        "DailyCheckIn": {
            "title": i18n.t("Reminder.DailyCheckIn.title", locale=locale),
            "body": i18n.t("Reminder.DailyCheckIn.body", locale=locale),
        },
        "RevereTest": {
            "title": i18n.t("Reminder.RevereTest.title", locale=locale),
            "body": i18n.t("Reminder.RevereTest.body", locale=locale),
        },
        "BMI": {
            "title": i18n.t("Reminder.BMI.title", locale=locale),
            "body": i18n.t("Reminder.BMI.body", locale=locale),
        },
        "Covid19RiskScore": {
            "title": i18n.t("Reminder.Covid19RiskScore.title", locale=locale),
            "body": i18n.t("Reminder.Covid19RiskScore.body", locale=locale),
        },
        "HealthScore": {
            "title": i18n.t("Reminder.HealthScore.title", locale=locale),
            "body": i18n.t("Reminder.HealthScore.body", locale=locale),
        },
        "Covid19DailyCheckIn": {
            "title": i18n.t("Reminder.Covid19DailyCheckIn.title", locale=locale),
            "body": i18n.t("Reminder.Covid19DailyCheckIn.body", locale=locale),
        },
        "RestingBreathingRate": {
            "title": i18n.t("Reminder.RestingBreathingRate.title", locale=locale),
            "body": i18n.t("Reminder.RestingBreathingRate.body", locale=locale),
        },
        "OxygenSaturation": {
            "title": i18n.t("Reminder.OxygenSaturation.title", locale=locale),
            "body": i18n.t("Reminder.OxygenSaturation.body", locale=locale),
        },
        "AwarenessTraining": {
            "title": i18n.t("Reminder.AwarenessTraining.title", locale=locale),
            "body": i18n.t("Reminder.AwarenessTraining.body", locale=locale),
        },
        "DiabetesDistressScore": {
            "title": i18n.t("Reminder.DiabetesDistressScore.title", locale=locale),
            "body": i18n.t("Reminder.DiabetesDistressScore.body", locale=locale),
        },
        "RespiratoryRate": {
            "title": i18n.t("Reminder.RespiratoryRate.title", locale=locale),
            "body": i18n.t("Reminder.RespiratoryRate.body", locale=locale),
        },
        "PeakFlow": {
            "title": i18n.t("Reminder.PeakFlow.title", locale=locale),
            "body": i18n.t("Reminder.PeakFlow.body", locale=locale),
        },
        "PregnancyStatus": {
            "title": i18n.t("Reminder.PregnancyStatus.title", locale=locale),
            "body": i18n.t("Reminder.PregnancyStatus.body", locale=locale),
        },
        "Medications": {
            "title": i18n.t("Reminder.Medications.title", locale=locale),
            "body": i18n.t("Reminder.Medications.body", locale=locale),
        },
        "HighFrequencyHeartRate": {
            "title": i18n.t("Reminder.HighFrequencyHeartRate.title", locale=locale),
            "body": i18n.t("Reminder.HighFrequencyHeartRate.body", locale=locale),
        },
        "ECGHealthKit": {
            "title": i18n.t("Reminder.ECGHealthKit.title", locale=locale),
            "body": i18n.t("Reminder.ECGHealthKit.body", locale=locale),
        },
        "AZGroupKeyActionTrigger": {
            "title": i18n.t("Reminder.AZGroupKeyActionTrigger.title", locale=locale),
            "body": i18n.t("Reminder.AZGroupKeyActionTrigger.body", locale=locale),
        },
        "HealthStatus": {
            "title": i18n.t("Reminder.HealthStatus.title", locale=locale),
            "body": i18n.t("Reminder.HealthStatus.body", locale=locale),
        },
        "FeverAndPainDrugs": {
            "title": i18n.t("Reminder.FeverAndPainDrugs.title", locale=locale),
            "body": i18n.t("Reminder.FeverAndPainDrugs.body", locale=locale),
        },
        "AdditionalQoL": {
            "title": i18n.t("Reminder.AdditionalQoL.title", locale=locale),
            "body": i18n.t("Reminder.AdditionalQoL.body", locale=locale),
        },
        "BackgroundInformation": {
            "title": i18n.t("Reminder.BackgroundInformation.title", locale=locale),
            "body": i18n.t("Reminder.BackgroundInformation.body", locale=locale),
        },
        "InfantFollowUp": {
            "title": i18n.t("Reminder.InfantFollowUp.title", locale=locale),
            "body": i18n.t("Reminder.InfantFollowUp.body", locale=locale),
        },
        "VaccinationDetails": {
            "title": i18n.t("Reminder.VaccinationDetails.title", locale=locale),
            "body": i18n.t("Reminder.VaccinationDetails.body", locale=locale),
        },
        "BreastFeedingUpdate": {
            "title": i18n.t("Reminder.BreastFeedingUpdate.title", locale=locale),
            "body": i18n.t("Reminder.BreastFeedingUpdate.body", locale=locale),
        },
        "BreastFeedingStatus": {
            "title": i18n.t("Reminder.BreastFeedingStatus.title", locale=locale),
            "body": i18n.t("Reminder.BreastFeedingStatus.body", locale=locale),
        },
        "PregnancyUpdate": {
            "title": i18n.t("Reminder.PregnancyUpdate.title", locale=locale),
            "body": i18n.t("Reminder.PregnancyUpdate.body", locale=locale),
        },
        "MedicalHistory": {
            "title": i18n.t("Reminder.MedicalHistory.title", locale=locale),
            "body": i18n.t("Reminder.MedicalHistory.body", locale=locale),
        },
        "OtherVaccine": {
            "title": i18n.t("Reminder.OtherVaccine.title", locale=locale),
            "body": i18n.t("Reminder.OtherVaccine.body", locale=locale),
        },
        "PregnancyFollowUp": {
            "title": i18n.t("Reminder.PregnancyFollowUp.title", locale=locale),
            "body": i18n.t("Reminder.PregnancyFollowUp.body", locale=locale),
        },
        "AZFurtherPregnancyKeyActionTrigger": {
            "title": i18n.t(
                "Reminder.AZFurtherPregnancyKeyActionTrigger.title", locale=locale
            ),
            "body": i18n.t(
                "Reminder.AZFurtherPregnancyKeyActionTrigger.body", locale=locale
            ),
        },
        "AZScreeningQuestionnaire": {
            "title": i18n.t("Reminder.AZScreeningQuestionnaire.title", locale=locale),
            "body": i18n.t("Reminder.AZScreeningQuestionnaire.body", locale=locale),
        },
        "PROMISGlobalHealth": {
            "title": i18n.t("Reminder.PROMISGlobalHealth.title", locale=locale),
            "body": i18n.t("Reminder.PROMISGlobalHealth.body", locale=locale),
        },
        "GeneralAnxietyDisorder": {
            "title": i18n.t("Reminder.GeneralAnxietyDisorder.title", locale=locale),
            "body": i18n.t("Reminder.GeneralAnxietyDisorder.body", locale=locale),
        },
        "SurgeryDetails": {
            "title": i18n.t("Reminder.SurgeryDetails.title", locale=locale),
            "body": i18n.t("Reminder.SurgeryDetails.body", locale=locale),
        },
    }


class Weekday(Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


@dataclass
class UserModuleReminder(CalendarEvent):
    REMINDER_ACTION = "REMINDER_OPEN_MODULE"

    DURATION_ISO = "durationIso"
    SPECIFIC_WEEK_DAYS = "specificWeekDays"
    SPECIFIC_MONTH_DAYS = "specificMonthDays"
    MODULE_ID = "moduleId"
    MODULE_CONFIG_ID = "moduleConfigId"

    EXTRA_FIELD_NAMES = (
        DURATION_ISO,
        SPECIFIC_MONTH_DAYS,
        SPECIFIC_WEEK_DAYS,
        MODULE_ID,
        MODULE_CONFIG_ID,
    )

    isRecurring: bool = field(default=True)
    durationIso: str = default_field(metadata=meta(validate_time_duration))
    specificWeekDays: list[Weekday] = default_field(
        metadata=meta(not_empty, value_to_field=remove_duplicates)
    )
    specificMonthDays: list[int] = default_field(
        metadata=meta(
            validate_min_max_month_days_list, value_to_field=remove_duplicates
        ),
    )
    moduleId: str = required_field(metadata=meta(not_empty))
    moduleConfigId: str = required_field()

    def execute(self, run_async=True):
        logger.debug(
            f"Sending {self.REMINDER_ACTION} notification for #{self.userId}/#{self.moduleId}"
        )
        if not self.title or not self.description:
            user = AuthorizationService().retrieve_simple_user_profile(
                user_id=self.userId
            )
            user = AuthorizedUser(user)
            locale = user.get_language()
            self.set_default_title_and_description(locale)

        notification_template = {"title": self.title, "body": self.description}
        notification_data = {
            "action": self.REMINDER_ACTION,
            "moduleId": self.moduleId,
            "moduleConfigId": self.moduleConfigId,
        }
        prepare_and_send_push_notification(
            user_id=self.userId,
            action=self.REMINDER_ACTION,
            notification_template=notification_template,
            notification_data=remove_none_values(notification_data),
            run_async=run_async,
        )

    def __str__(self):
        return f"UserModuleReminder[{self.moduleId}] at {self.durationIso}"

    def pack_extra_fields(self):
        extra_fields = {}
        for field_name in self.EXTRA_FIELD_NAMES:
            value = getattr(self, field_name, None)
            if field_name == self.SPECIFIC_WEEK_DAYS and value:
                value = list(map(lambda x: x.value, value))
            extra_fields[field_name] = value
            setattr(self, field_name, None)
        self.extraFields = remove_none_values(extra_fields)

    def build_rrule_from_duration_iso(self):
        """Create rrule from durationIso and start/end datetime."""
        if self.isRecurring:
            start_time = get_time_from_duration_iso(self.durationIso)
            start_date = utc_str_val_to_field(self.startDateTime)
            rrule_dict = {
                "byhour": int(start_time.hour),
                "byminute": int(start_time.minute),
                "dtstart": utc_str_val_to_field(start_date),
            }

            if self.endDateTime:
                rrule_dict.update({"until": utc_str_val_to_field(self.endDateTime)})

            if self.specificWeekDays:
                if len(self.specificWeekDays) == 7:
                    rrule_dict.update({"freq": rrule.DAILY})
                else:
                    rrule_dict.update(
                        {
                            "byweekday": map(
                                lambda x: list(Weekday).index(x), self.specificWeekDays
                            ),
                            "freq": rrule.WEEKLY,
                        }
                    )
            elif self.specificMonthDays:
                rrule_dict.update(
                    {"bymonthday": self.specificMonthDays, "freq": rrule.MONTHLY}
                )
            self.recurrencePattern = str(rrule.rrule(**rrule_dict))

    def get_config_notification_data(self) -> NotificationData:
        service = DeploymentService()
        module_config = service.retrieve_module_config(self.moduleConfigId)

        if module_config and module_config.notificationData:
            return module_config.notificationData

    def set_default_title_and_description(self, language: str):
        if self.title and self.description:
            return

        template_from_config = self.get_config_notification_data()
        if (
            template_from_config
            and template_from_config.title
            and template_from_config.body
        ):
            self.title = i18n.t(template_from_config.title, locale=language)
            self.description = i18n.t(template_from_config.body, locale=language)
            return

        if title_and_body := self.get_static_reminder_templates(language):
            self.title = title_and_body[NotificationData.TITLE]
            self.description = title_and_body[NotificationData.BODY]

    @deprecated("Use `moduleConfig.notificationData` instead.")
    def get_static_reminder_templates(self, language) -> dict:
        """
        Old way to get notification data for module.
        @deprecated Use `moduleConfig.notificationData` instead.
        @return: dict of title and body keys with translated values
        """
        reminder_templates = get_reminder_notification_templates(language)
        reminder_templates = reminder_templates.get(self.moduleId)
        return reminder_templates or None

    def _set_start_date_time(self):
        if self.startDateTime:
            date = utc_str_val_to_field(self.startDateTime)
        else:
            date = datetime.utcnow()

        self.startDateTime = utc_str_field_to_val(date.replace(second=0, microsecond=0))


class ReminderAction(Enum):
    CreateModuleReminder = "CreateModuleReminder"
    UpdateModuleReminder = "UpdateModuleReminder"
    DeleteModuleReminder = "DeleteModuleReminder"
