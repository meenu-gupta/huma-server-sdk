import logging

from celery.schedules import crontab

from sdk.celery.app import celery_app
from sdk.common.constants import SEC_IN_HOUR

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=30),
        calculate_stats_per_user.s(),
        name="User stats calculator",
    )


def calculate_stats_for_user(task):
    (
        user,
        AuthorizationService,
        UserStatsCalculator,
        UpdateUserProfileRequestObject,
    ) = task
    service = AuthorizationService()
    stats = UserStatsCalculator(user).run()
    data = {
        UpdateUserProfileRequestObject.ID: user.id,
        UpdateUserProfileRequestObject.STATS: stats,
    }
    req_obj = UpdateUserProfileRequestObject.from_dict(data)
    service.update_user_profile(req_obj)


@celery_app.task(expires=SEC_IN_HOUR)
def calculate_stats_per_user(*args):
    from concurrent.futures import ThreadPoolExecutor
    from extensions.authorization.services.authorization import AuthorizationService
    from extensions.authorization.models.stats_calculator import UserStatsCalculator
    from extensions.authorization.router.user_profile_request import (
        UpdateUserProfileRequestObject,
    )

    service = AuthorizationService()
    users = service.retrieve_users_with_user_role_including_only_fields(("timezone",))

    tasks = [
        (
            user,
            AuthorizationService,
            UserStatsCalculator,
            UpdateUserProfileRequestObject,
        )
        for user in users
    ]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(calculate_stats_for_user, tasks)
