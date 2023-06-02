from datetime import datetime

import pymongo
from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.database import Database

from extensions.exceptions import MedicationDoesNotExist
from extensions.medication.models.medication import Medication
from extensions.medication.repository.medication_repository import MedicationRepository
from sdk.common.utils.inject import autoparams
from sdk.common.utils.validators import remove_none_values, id_as_obj_id


class MongoMedicationRepository(MedicationRepository):
    MEDICATION_COLLECTION = "medication"

    @autoparams()
    def __init__(self, database: Database):
        self._db = database

    def create_medication(self, medication: Medication) -> str:
        medication.createDateTime = medication.updateDateTime = datetime.utcnow()
        medication_dict = remove_none_values(
            medication.to_dict(
                ignored_fields=(
                    Medication.CREATE_DATE_TIME,
                    Medication.UPDATE_DATE_TIME,
                )
            )
        )
        medication_dict[Medication.CHANGE_HISTORY] = [
            {
                **medication_dict,
                "changeType": "MEDICATION_CREATE",
            }
        ]
        inserted_id = (
            self._db[self.MEDICATION_COLLECTION].insert_one(medication_dict).inserted_id
        )
        return str(inserted_id)

    @id_as_obj_id
    def retrieve_medications(
        self,
        skip: int,
        limit: int,
        user_id: str,
        start_date: datetime,
        only_enabled: bool = True,
        end_date: datetime = None,
        direction: int = pymongo.ASCENDING,
    ) -> list[Medication]:
        options = {Medication.USER_ID: user_id}
        if start_date and end_date:
            options["$and"] = [
                {Medication.UPDATE_DATE_TIME: {"$gte": start_date}},
                {Medication.UPDATE_DATE_TIME: {"$lte": end_date}},
            ]
        elif start_date:
            options[Medication.UPDATE_DATE_TIME] = {"$gte": start_date}
        elif end_date:
            options[Medication.UPDATE_DATE_TIME] = {"$lte": end_date}

        # excludes deleted records if needed
        if only_enabled:
            options.update({Medication.ENABLED: True})

        medications = (
            self._db[self.MEDICATION_COLLECTION]
            .find(options)
            .skip(skip)
            .limit(limit)
            .sort(Medication.CREATE_DATE_TIME, direction)
        )
        result = []
        for medication in medications:
            medication[Medication.ID] = str(medication.pop(Medication.ID_))
            result.append(Medication.from_dict(medication))
        return result

    @id_as_obj_id
    def retrieve_medication_by_id(self, medication_id: str) -> Medication:
        medication = self._db[self.MEDICATION_COLLECTION].find_one(
            {Medication.ID_: medication_id}
        )
        if not medication:
            raise MedicationDoesNotExist
        medication[Medication.ID] = str(medication[Medication.ID_])
        return Medication.from_dict(medication)

    def update_medication(self, medication: Medication) -> str:
        medication.updateDateTime = datetime.utcnow()
        medication_dict = remove_none_values(
            medication.to_dict(
                ignored_fields=(
                    Medication.CREATE_DATE_TIME,
                    Medication.UPDATE_DATE_TIME,
                )
            )
        )
        medication_id = ObjectId(medication_dict.pop(Medication.ID))

        updated_result = self._db[self.MEDICATION_COLLECTION].update_one(
            {
                Medication.ID_: medication_id,
                Medication.USER_ID: ObjectId(medication.userId),
            },
            {
                "$set": remove_none_values(medication_dict),
                "$push": {
                    Medication.CHANGE_HISTORY: {
                        **medication_dict,
                        "changeType": self._set_change_type(medication_dict),
                    }
                },
            },
        )
        if updated_result.modified_count == 0:
            raise MedicationDoesNotExist

        return str(medication_id)

    @staticmethod
    def _set_change_type(medication_dict):
        change_type = "MEDICATION_UPDATE"
        if medication_dict.get(Medication.ENABLED, None) is False:
            change_type = "MEDICATION_DELETE"
        return change_type

    @id_as_obj_id
    def delete_user_medication(self, user_id: str, session: ClientSession = None):
        self._db[self.MEDICATION_COLLECTION].delete_many(
            {Medication.USER_ID: user_id}, session=session
        )
