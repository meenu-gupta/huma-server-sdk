import pymongo

from extensions.medication.models.medication import Medication
from extensions.medication.repository.medication_repository import MedicationRepository
from extensions.module_result.modules.visualizer import HTMLVisualizer
from sdk.common.utils.inject import autoparams

_units_map = {
    "application": "Applications",
    "bottle": "Bottles",
    "capsule": "Capsules",
    "carton": "Cartons",
    "drop": "Drops",
    "gram": "Grams",
    "gargle": "Gargles",
    "internationalUnit": "International units",
    "microgram": "Micrograms",
    "milligram": "Milligrams",
    "microgramHr": "Micrograms/hr",
    "microgram24Hr": "Micrograms/24hr",
    "milliliter": "Milliliters",
    "patch": "Patches",
    "puffs": "Puffs",
    "rinse": "Rinses",
    "serving": "Servings",
    "spray": "Sprays",
    "suppository": "Suppositories",
    "tablet": "Tablets",
    "unit": "Units",
    "other": "Others",
}


class MedicationVisualizer(HTMLVisualizer):
    TITLE = "Medication"
    template_name = "medication.html"

    def get_context(self) -> dict:
        config = self.module.find_config(self.deployment.moduleConfigs, None)
        if not config:
            return {}

        with self.module.configure(config):
            medications: list[Medication] = self._fetch_medications()
            if not medications:
                return {}

        current_medications, old_medications = self._split_medications(medications)
        medications_current_data = self._get_medications(current_medications)
        medications_old_data = self._get_medications(old_medications)
        if not medications_current_data and not medications_old_data:
            return {}

        return {
            "medication_title": config.moduleName or self.TITLE,
            "current_data": medications_current_data,
            "old_data": medications_old_data,
        }

    def _get_medications(self, medications: list[Medication]) -> dict:
        medications_data = {}
        for medication in medications:
            year = str(medication.updateDateTime.year)
            month = medication.updateDateTime.strftime("%b")
            if year not in medications_data:
                medications_data[year] = {}

            if month not in medications_data[year]:
                medications_data[year][month] = []

            medications_data[year][month].append(self.model_to_view(medication))

        return medications_data

    def model_to_view(self, medication: Medication) -> dict:
        frequency = "As needed"
        if medication.schedule:
            frequency = medication.schedule.get_frequency_str()

        return {
            "name": medication.name,
            "dosage": medication.doseQuantity,
            "unit": _units_map.get(medication.doseUnits, medication.doseUnits),
            "frequency": frequency,
        }

    @autoparams("repo")
    def _fetch_medications(self, repo: MedicationRepository) -> list[Medication]:
        medications = repo.retrieve_medications(
            skip=0,
            limit=int(10e6),
            user_id=self.user.id,
            start_date=self.start_date_time,
            only_enabled=False,
            end_date=self.end_date_time,
            direction=pymongo.DESCENDING,
        )
        self._apply_timezone_to_medications(medications)
        return medications

    @staticmethod
    def _split_medications(
        medications: list[Medication],
    ) -> tuple[list[Medication], ...]:
        current_medications = []
        old_medications = []
        for medication in medications:
            target = current_medications if medication.enabled else old_medications
            if len(target) >= 25:
                continue
            target.append(medication)
        return current_medications, old_medications

    def _apply_timezone_to_medications(self, meds: list[Medication]) -> None:
        for med in meds:
            med.updateDateTime = med.updateDateTime.astimezone(self.timezone)
            med.createDateTime = med.createDateTime.astimezone(self.timezone)
