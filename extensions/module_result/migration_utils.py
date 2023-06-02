from collections import defaultdict
from datetime import datetime
from extensions.module_result.calculate_unseen_and_recent_flags import UserFlagsStats

import pymongo
import logging

from bson import ObjectId

from extensions.authorization.models.user import User
from extensions.deployment.models.deployment import (
    DeploymentRevision,
    ChangeType,
    Deployment,
)
from extensions.module_result.models.primitives import (
    EQ5D5L,
    Primitive,
    QuestionnaireAnswer,
    Questionnaire,
)
from extensions.module_result.modules import EQ5D5LModule
from extensions.module_result.questionnaires import EQ5DQuestionnaireCalculator

eq_5d_5l_module_collection = EQ5D5L.__name__.lower()
module_name_in_questionnaire = "EQ-5D-5L"
eq5_attrs = set(EQ5D5L.__annotations__.keys())
primitive_attrs = set(Primitive.__annotations__.keys())

logger = logging.getLogger(__name__)


def migrate_eq5_to_new_structure(db):
    eq_records = list(
        db.get_collection("questionnaire").find(
            {
                "questionnaireName": module_name_in_questionnaire,
                "moduleId": "Questionnaire",
            }
        )
    )
    eq_module_config_ids = {r["moduleConfigId"] for r in eq_records}

    deployments_with_module = db["deployment"].find(
        {"moduleConfigs.id": {"$in": list(eq_module_config_ids)}}
    )
    deployment_revision_data = []
    processed_module_cfgs = set()
    num_of_migrated_records = 0
    records_to_create = defaultdict(dict)
    for deployment in deployments_with_module:
        for module_config in deployment["moduleConfigs"]:
            module_cfg_id = module_config.get("id", "")

            if module_cfg_id not in eq_module_config_ids:
                continue

            records = [r for r in eq_records if module_cfg_id == r["moduleConfigId"]]
            if not records:
                continue

            for db_record in records:
                record = _prepare_eq_record(db_record, module_config["configBody"])
                record_id = db_record[Questionnaire.ID_]
                _update_answer_ids_in_questionnaire(db, record_id, db_record)
                records_to_create[module_cfg_id][str(record_id)] = record
            data = list(records_to_create[module_cfg_id].values())
            db[eq_5d_5l_module_collection].insert_many(data)
            logger.info(f"Updated {len(data)} records for config: {module_cfg_id}")
            processed_module_cfgs.add(module_cfg_id)
            num_of_migrated_records += len(data)

        dt_now = datetime.utcnow()
        deployment_revision_data.append(
            {
                DeploymentRevision.CHANGE_TYPE: ChangeType.MODULE_CONFIG.value,
                DeploymentRevision.VERSION: deployment[Deployment.VERSION],
                DeploymentRevision.DEPLOYMENT_ID: deployment[Deployment.ID_],
                DeploymentRevision.SNAP: deployment,
                DeploymentRevision.UPDATE_DATE_TIME: dt_now,
                DeploymentRevision.CREATE_DATE_TIME: dt_now,
            }
        )

    unprocessed_module_ids = eq_module_config_ids - processed_module_cfgs
    if unprocessed_module_ids:
        revision_records = _process_records_from_deployment_revisions(
            db, eq_records, unprocessed_module_ids
        )
        num_of_migrated_records += sum([len(v) for v in revision_records.values()])
        records_to_create.update(revision_records)
    logger.info(f"Num of migrated records: {num_of_migrated_records}")

    _update_deployments_config(db, eq_module_config_ids)
    _create_revision(db, deployment_revision_data)
    _update_module_id_in_questionnaires(db, eq_module_config_ids)
    _update_recent_module_results(db, records_to_create)
    UserFlagsStats(db).calculate()


def _process_records_from_deployment_revisions(
    db, eq_records: list[dict], unprocessed_module_ids: set[ObjectId]
) -> dict:
    records_to_create = defaultdict(dict)
    not_found_module_ids_in_revision = set()
    num_not_migrated_users = 0
    not_not_migrated_records = 0
    for m_id in unprocessed_module_ids:
        deployments_revision = [
            r
            for r in db["deploymentrevision"]
            .find({"snap.moduleConfigs.id": m_id})
            .sort([("createDateTime", pymongo.ASCENDING)])
        ]
        if not deployments_revision:
            not_found_module_ids_in_revision.add(m_id)
            records = [r for r in eq_records if m_id == r["moduleConfigId"]]
            not_not_migrated_records += len(records)
            num_not_migrated_users += len({r["userId"] for r in records})
            continue

        deployment = deployments_revision[-1].get("snap")
        for module_config in deployment["moduleConfigs"]:
            module_cfg_id = module_config.get("id", "")
            if module_cfg_id not in unprocessed_module_ids:
                continue

            records = [r for r in eq_records if module_cfg_id == r["moduleConfigId"]]
            if not records:
                continue

            for db_record in records:
                record = _prepare_eq_record(db_record, module_config["configBody"])
                record_id = db_record[Questionnaire.ID_]
                _update_answer_ids_in_questionnaire(db, record_id, db_record)
                records_to_create[module_cfg_id][str(record_id)] = record
            data = list(records_to_create[module_cfg_id].values())
            db[eq_5d_5l_module_collection].insert_many(data)

    if records_to_create:
        db[eq_5d_5l_module_collection].insert_many(list(records_to_create.values()))

    if not_found_module_ids_in_revision:
        logger.warning(f"Unprocessed module ids: {not_found_module_ids_in_revision}")
        logger.warning(f"Unprocessed num of users: {num_not_migrated_users}")
        logger.warning(f"Unprocessed num of records: {not_not_migrated_records}")
    return records_to_create


def _update_deployments_config(db, module_ids: set[ObjectId]):
    if not module_ids:
        return
    db.get_collection("deployment").update_many(
        {"moduleConfigs.id": {"$in": list(module_ids)}},
        {
            "$set": {
                "moduleConfigs.$.configBody.pages": [],
                "moduleConfigs.$.configBody.submissionPage": {},
                "moduleConfigs.$.moduleId": EQ5D5LModule.moduleId,
                "moduleConfigs.$.configBody.toggleIndexValue": True,
                "updateDateTime": datetime.utcnow(),
            },
            "$inc": {Deployment.VERSION: 1},
            "$unset": {"moduleConfigs.$.configBody.questionnaireType": ""},
        },
    )


def _update_module_id_in_questionnaires(db, module_cfg_ids: set[ObjectId]):
    if not module_cfg_ids:
        return
    filter_query = {"moduleConfigId": {"$in": list(module_cfg_ids)}}
    update_query = {"$set": {"moduleId": EQ5D5LModule.moduleId}}
    db.get_collection("questionnaire").update_many(filter_query, update_query)
    db.get_collection("unseenrecentresult").update_many(filter_query, update_query)


def _update_recent_module_results(db, created_records: dict):
    if not created_records:
        return
    user_collection = db.get_collection("user")
    for config_id, config_records in created_records.items():
        config_id = str(config_id)
        users = user_collection.find(
            {f"recentModuleResults.{config_id}": {"$exists": True}}
        )
        for user in users:
            recent_results = user[User.RECENT_MODULE_RESULTS].get(config_id)
            for result in recent_results:
                questionnaire = result.get(Questionnaire.__name__)
                if not questionnaire:
                    continue
                questionnaire_id = questionnaire.get(Questionnaire.ID)
                questionnaire[Questionnaire.MODULE_ID] = EQ5D5LModule.moduleId
                _update_rag(questionnaire)
                record = config_records.get(questionnaire_id)
                if not record:
                    continue
                record[EQ5D5L.ID] = str(record.pop(EQ5D5L.ID_))
                recent_eq5_record = {EQ5D5L.__name__: record}
                result.update(recent_eq5_record)
            filter_query = {User.ID_: user[User.ID_]}
            update_query = {
                "$set": {User.RECENT_MODULE_RESULTS: user[User.RECENT_MODULE_RESULTS]}
            }
            user_collection.update(filter_query, update_query)


def _update_rag(record: dict):
    if not (rag := record.get(Questionnaire.RAG_THRESHOLD)):
        return record
    rag_value = rag.pop(Questionnaire.__name__, {})
    record[Questionnaire.RAG_THRESHOLD][EQ5D5L.__name__] = rag_value
    return record


def _update_answer_ids_in_questionnaire(
    db, questionnaire_id: ObjectId, db_record: dict
):
    answers = db_record[Questionnaire.ANSWERS]
    question_ids = [
        "hu_eq5d5l_mobility",
        "hu_eq5d5l_selfcare",
        "hu_eq5d5l_usualactivity",
        "hu_eq5d5l_paindiscomfort",
        "hu_eq5d5l_anxiety",
        "hu_eq5d5l_scale",
    ]
    for index, answer in enumerate(answers[:6]):
        answer["questionId"] = question_ids[index]
    db.get_collection("questionnaire").update_one(
        {"_id": questionnaire_id},
        {
            "$set": {
                Questionnaire.ANSWERS: answers,
                Questionnaire.RAG_THRESHOLD: db_record.get(Questionnaire.RAG_THRESHOLD),
            }
        },
    )


def _create_revision(db, revision_data: list[dict]):
    if not revision_data:
        return
    db["deploymentrevision"].insert_many(revision_data)


def _prepare_eq_record(db_record: dict, config_body: dict) -> dict:
    record_to_create = {EQ5D5L.ID_: db_record[Questionnaire.ID_]}
    db_record = _update_rag(db_record)
    for key, value in db_record.items():
        if key in eq5_attrs or key in primitive_attrs:
            record_to_create[key] = value

    answers = [QuestionnaireAnswer.from_dict(a) for a in db_record["answers"]]
    scores = EQ5DQuestionnaireCalculator.build_eq5d5l_scores(config_body, answers)

    record_to_create[EQ5D5L.MODULE_ID] = EQ5D5LModule.moduleId
    return {**record_to_create, **scores}
