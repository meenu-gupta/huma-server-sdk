from extensions.module_result.modules.module import Module
from extensions.module_result.models.primitives import Covid19DailyCheckIn


class Covid19DailyCheckInModule(Module):
    moduleId = "Covid19DailyCheckIn"
    primitives = [Covid19DailyCheckIn]
