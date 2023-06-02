from extensions.module_result.modules.questionnaire import QuestionnaireModule
from extensions.module_result.models.primitives import Questionnaire


class BreathlessnessModule(QuestionnaireModule):
    moduleId = "Breathlessness"
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
                if self._is_value_correct(value):
                    primitive.value = value

    @staticmethod
    def _is_value_correct(value):
        return 1 <= value <= 5
