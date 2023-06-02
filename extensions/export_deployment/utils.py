import logging
from i18n import t
from mongoengine import DynamicDocument
from pymongo import MongoClient
from pymongo.database import Database

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.repository.auth_repository import AuthorizationRepository
from extensions.common.monitoring import report_exception
from extensions.export_deployment.email_notification import EmailUserExportStatusService
from extensions.export_deployment.models.export_deployment_models import ExportProcess
from sdk.common.push_notifications.push_notifications_utils import (
    prepare_and_send_push_notification,
)
from sdk.common.utils import inject
from sdk.common.utils.inject import autoparams
from sdk.common.utils.mongo_utils import convert_values


logger = logging.getLogger("export_push")


class SourceMongoClient(MongoClient):
    pass


class SourceDatabase(Database):
    pass


class SourceMongoPhoenixDocument(DynamicDocument):
    meta = {"allow_inheritance": True, "abstract": True}

    @classmethod
    def _get_db(cls):
        return inject.instance(SourceDatabase)

    def to_dict(self):
        _dict = self.to_mongo()
        _dict = convert_values(_dict)
        return _dict


def _get_affected_process_pipeline():
    return [
        {
            "$lookup": {
                "from": "user",
                "localField": "requesterId",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": {"path": "$user"}},
        {"$addFields": {"role": "$user.roles.roleId"}},
        {"$unwind": {"path": "$role"}},
        {"$match": {"role": "User"}},
        {"$group": {"_id": None, "ids": {"$push": "$_id"}}},
    ]


def set_proper_export_type(db: Database):
    pipeline = _get_affected_process_pipeline()
    export_process_collection = db.get_collection("exportprocess")
    affected_processes = list(export_process_collection.aggregate(pipeline))
    if not affected_processes:
        return
    search_query = {"_id": {"$in": affected_processes[0]["ids"]}}
    update_query = {
        "$set": {ExportProcess.EXPORT_TYPE: ExportProcess.ExportType.USER.value}
    }
    updated = export_process_collection.update_many(search_query, update_query)
    print(f"Updated: {updated.modified_count}")


def _notify_user_on_success_data_generation(*user_data):
    user_id, _, _, locale = user_data
    send_push_notification(user_id, locale)
    EmailUserExportStatusService().send_success_data_generation_email(*user_data)


def _notify_user_on_failed_data_generation(*user_data):
    user_id, _, _, locale = user_data
    send_push_notification(user_id, locale, is_error=True)
    EmailUserExportStatusService().send_failure_data_generation_email(*user_data)


@autoparams("auth_repo")
def _get_user_data(user_id, auth_repo: AuthorizationRepository):
    user = auth_repo.retrieve_user(user_id=user_id)
    auth_user = AuthorizedUser(auth_repo.retrieve_user(user_id=user_id))
    locale = auth_user.get_language()
    return user.id, user.givenName, user.email, locale


def send_push_notification(user_id: str, locale: str, is_error: bool = False):
    action = "OPEN_DOWNLOAD_DATA"
    try:
        if is_error:
            body = t("DataPushNotification.failBody", locale=locale)
        else:
            body = t("DataPushNotification.successBody", locale=locale)

        logger.debug(f"Sending Download notification for #{user_id}")
        title = t("DataPushNotification.title", locale=locale)
        notification_template = {"title": title, "body": body}
        prepare_and_send_push_notification(
            user_id,
            action,
            notification_template,
            run_async=True,
        )
    except Exception as error:
        report_exception(
            error,
            context_name="PDFExport",
            context_content={
                "userId": user_id,
                "locale": locale,
                "action": action,
            },
        )


def notify_user_on_export_status(process: ExportProcess, is_error=False):
    user_export_types = [
        ExportProcess.ExportType.USER,
        ExportProcess.ExportType.SUMMARY_REPORT,
    ]
    if not (
        process.exportType in user_export_types
        and process.requesterId in process.exportParams.userIds
    ):
        return

    user_data = _get_user_data(process.requesterId)
    if is_error:
        _notify_user_on_failed_data_generation(*user_data)
    else:
        _notify_user_on_success_data_generation(*user_data)
