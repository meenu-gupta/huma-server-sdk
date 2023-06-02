from collections import defaultdict

from extensions.deployment.models.consent.consent_log import ConsentLog
from extensions.export_deployment.helpers.convertion_helpers import (
    convert_id_fields_to_string,
    ExportData,
)
from extensions.export_deployment.use_case.exportable.exportable_use_case import (
    ExportableUseCase,
)
from extensions.module_result.models.primitives import Primitive


class ConsentExportableUseCase(ExportableUseCase):
    onboardingModuleName = "Consent"

    def get_raw_result(self) -> ExportData:
        onboarding_modules = self.request_object.onboardingModuleNames
        if (
            not onboarding_modules
            or self.onboardingModuleName not in onboarding_modules
        ):
            return {}
        if not self.request_object.deployment.consent:
            return {}

        consent_logs = self._export_repo.retrieve_consent_logs(
            consent_id=self.request_object.deployment.consent.id,
            start_date=self.request_object.fromDate,
            end_date=self.request_object.toDate,
            user_ids=self.request_object.userIds,
            use_creation_time=self.request_object.useCreationTime,
        )

        final_results = defaultdict(list)

        for consent_log in consent_logs:
            primitive_dict = self.get_consent_dict(consent_log)
            final_results[self.onboardingModuleName].append(primitive_dict)
        return final_results

    def get_consent_dict(self, primitive: ConsentLog) -> dict:
        """Converts primitive object to dictionary and convert ObjectIds"""
        data = primitive.to_dict(
            ignored_fields=(
                ConsentLog.USER_ID,
                ConsentLog.DEPLOYMENT_ID,
                ConsentLog.CONSENT_ID,
            )
        )

        data[Primitive.CLS] = primitive.__class__.__name__
        data[Primitive.MODULE_ID] = self.onboardingModuleName
        data[Primitive.START_DATE_TIME] = data.get(ConsentLog.CREATE_DATE_TIME)

        data = convert_id_fields_to_string(data)
        return data
