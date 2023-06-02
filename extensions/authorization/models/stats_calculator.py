from collections import defaultdict
from datetime import datetime, timedelta

from extensions.authorization.models.user import User, UserStats, TaskCompliance
from extensions.key_action.models.key_action_log import KeyAction
from sdk.calendar.service.calendar_service import CalendarService


class UserStatsCalculator:
    def __init__(self, user: User):
        self.user = user
        self._calendar_service = CalendarService()
        self.all_events = self._retrieve_events()
        self.now = datetime.utcnow()

    def _retrieve_events(self) -> list[dict]:
        return self._calendar_service.retrieve_all_calendar_events(
            timezone=self.user.timezone,
            userId=self.user.id,
            model=KeyAction.__name__,
            to_model=False,
        )

    def run(self):
        task_compliance = {
            TaskCompliance.TOTAL: len(self.all_events),
            TaskCompliance.CURRENT: self.retrieve_completed_key_actions(),
            TaskCompliance.DUE: self.retrieve_expiring_key_actions(),
            TaskCompliance.UPDATE_DATE_TIME: datetime.utcnow(),
        }
        # Calculating  weeklyProgress
        weekly_progress_list = self.retrieve_grouped_period_key_actions()

        study_progress = {
            TaskCompliance.CURRENT_PERIOD: len(weekly_progress_list) + 1,
            TaskCompliance.TOTAL_PERIOD: len(self.all_events),
            TaskCompliance.TOTAL_COMPLIANCE: round(
                (self.retrieve_completed_key_actions() / len(self.all_events)) * 100
            ),
            TaskCompliance.PERIOD_PROGRESS: weekly_progress_list,
        }

        return UserStats.from_dict(
            {
                UserStats.TASK_COMPLIANCE: task_compliance,
                UserStats.STUDY_PROGRESS: study_progress,
            }
        )

    def retrieve_completed_key_actions(self) -> int:
        return len([event for event in self.all_events if not event.get("enabled")])

    def retrieve_grouped_period_key_actions(self) -> int:
        study_list = self.all_events
        weekly_progress_list = {}
        for study in study_list:
            if not study.get("enabled"):
                if (
                    TaskCompliance.COMPLETED_KEY_ACTIONS
                    in weekly_progress_list[study.get(TaskCompliance.CREATE_DATE_TIME)]
                ):
                    weekly_progress_list[study.get(TaskCompliance.CREATE_DATE_TIME)][
                        TaskCompliance.COMPLETED_KEY_ACTIONS
                    ] += 1
                else:
                    weekly_progress_list[study.get(TaskCompliance.CREATE_DATE_TIME)][
                        TaskCompliance.COMPLETED_KEY_ACTIONS
                    ] = 0

            if (
                TaskCompliance.ALL_KEY_ACTIONS
                in weekly_progress_list[study.get(TaskCompliance.CREATE_DATE_TIME)]
            ):
                weekly_progress_list[study.get(TaskCompliance.CREATE_DATE_TIME)][
                    TaskCompliance.ALL_KEY_ACTIONS
                ] += 1
            else:
                weekly_progress_list[study.get(TaskCompliance.CREATE_DATE_TIME)][
                    TaskCompliance.ALL_KEY_ACTIONS
                ] = 0

        for period in weekly_progress_list:
            completedKeyactions = weekly_progress_list[period].pop(
                TaskCompliance.COMPLETED_KEY_ACTIONS
            )
            allKeyActions = weekly_progress_list[period].pop(
                TaskCompliance.ALL_KEY_ACTIONS
            )
            percentage = round((completedKeyactions / allKeyActions) * 100)
            weekly_progress_list[TaskCompliance.TOTAL_COMPLIANCE] = percentage
            weekly_progress_list[TaskCompliance.START_DATE_TIME] = period

        return weekly_progress_list

    def retrieve_expiring_key_actions(self) -> int:
        events = self._calendar_service.retrieve_calendar_events_between_two_dates(
            start=self.now,
            end=self.now + timedelta(hours=48),
            timezone=self.user.timezone,
            expiring=True,
            userId=self.user.id,
            model=KeyAction.__name__,
            to_model=False,
        )
        return len([event for event in events if event.get("enabled")])
