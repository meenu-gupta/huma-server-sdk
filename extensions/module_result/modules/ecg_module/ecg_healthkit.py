import datetime
from numbers import Number

import i18n

from extensions.authorization.models.authorized_user import AuthorizedUser
from extensions.authorization.models.user import User
from extensions.module_result.modules.module import Module
from extensions.module_result.modules.ecg_module.service.ecg_healthkit_service import (
    ECGHealthKitService,
)
from extensions.module_result.common.flatbuffer_utils import ecg_data_points_to_array
from extensions.module_result.models.primitives import (
    ECGHealthKit,
    ECGClassification,
)


class ECGHealthKitModule(Module):
    moduleId = "ECGHealthKit"
    primitives = [ECGHealthKit]
    ragEnabled = True

    def preprocess(self, primitives: list[ECGHealthKit], user: User):
        if not primitives:
            return
        for primitive in primitives:
            if type(primitive) is ECGHealthKit:
                data_points = ecg_data_points_to_array(primitive.ecgReading.dataPoints)
                primitive.generatedPDF = self._generate_ecg_pdf(
                    primitive.value,
                    user,
                    data_points,
                    primitive.ecgReading.averageHeartRate,
                    primitive.startDateTime,
                )

    def _generate_ecg_pdf(
        self, value: int, user: User, data: list, average_bpm: Number, time: datetime
    ):
        classification = self._get_localized_classification(value, user)
        return ECGHealthKitService().generate_and_save_ecg_pdf_to_bucket(
            user, data, average_bpm, time, classification
        )

    @staticmethod
    def _get_localized_classification(value: int, user: User) -> str:
        user: AuthorizedUser = AuthorizedUser(user)
        locale = user.get_language()
        classification = ECGClassification(value).name
        return i18n.t(f"ECG.{classification}", locale=locale)
