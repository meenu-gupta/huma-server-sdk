from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.models.primitives import Questionnaire


class DailyCheckInModule(QuestionnaireModule):
    moduleId = "DailyCheckIn"
    primitives = [Questionnaire]
    validation_schema_path = "./schemas/questionnaire_schema.json"
    ragEnabled = True

    def calculate(self, primitive: Questionnaire):
        if primitive.answers:
            try:
                value = int(primitive.answers[0].answerText)
            except ValueError:
                pass
            else:
                primitive.value = value
