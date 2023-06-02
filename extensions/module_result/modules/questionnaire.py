import logging
import re
from pathlib import Path
from typing import Iterator, Optional, Type

from extensions.authorization.models.user import User
from extensions.module_result.models.module_config import ModuleConfig
from extensions.module_result.models.primitives import (
    Questionnaire,
    Primitive,
    QuestionnaireAnswer,
)
from extensions.module_result.models.primitives.primitive_questionnaire import (
    PageType,
    QuestionAnswerFormat,
    QuestionAnswerSelectionCriteria,
    QuestionConfig,
)
from extensions.module_result.module_result_utils import config_body_to_question_map
from extensions.module_result.modules.module import Module
from extensions.module_result.questionnaires import QuestionnaireCalculator
from extensions.module_result.questionnaires.questionnaire_answer_validator import (
    QuestionnaireAnswerValidator,
)
from extensions.module_result.questionnaires.questionnaire_factory import (
    QuestionnaireCalculatorFactory,
)
from sdk.common.exceptions.exceptions import InvalidRequestException
from sdk.common.utils.common_functions_utils import find
from sdk.common.utils.convertible import ConvertibleClassValidationError
from sdk.common.utils.validators import read_json_file, validate_object_id

logger = logging.getLogger(__file__)


class QuestionnaireModule(Module):
    QUESTIONNAIRE_TYPE = "questionnaireType"

    moduleId = "Questionnaire"
    primitives = [Questionnaire]
    calculator: Type[QuestionnaireCalculator] = None
    validation_schema_path = "./schemas/questionnaire_schema.json"
    ragEnabled = True

    def preprocess(self, primitives: list[Primitive], user: Optional[User]):
        for primitive in primitives:
            self._validate_questionnaire_answers(primitive)
            if isinstance(primitive, Questionnaire):
                self._preprocess_questionnaire_answers(primitive.answers)

        super().preprocess(primitives, user)

    def _validate_questionnaire_answers(self, primitive: Primitive):
        # TODO remove validation blocker
        # this is a fix for backward compatibility for apps before 1.17
        # ticket https://medopadteam.atlassian.net/browse/DEV-3643
        # TODO unlock test `test_submit_with_numeric_validation`
        # TODO unlock test `test_media_questionnaire_validation_errors`
        return

        if not isinstance(primitive, Questionnaire):
            return

        self._check_for_duplicate_answers(primitive)
        for answer in primitive.answers:
            QuestionnaireAnswerValidator(self.config.configBody).validate_answer(answer)

    @staticmethod
    def _check_for_duplicate_answers(raw_data: Questionnaire):
        if not (answers := raw_data.answers):
            return

        question_ids = {answer.questionId for answer in answers}
        if all(question_ids):
            if len(answers) == len(question_ids):
                return
        else:
            questions = {answer.question for answer in answers}
            if len(answers) == len(questions):
                return

        raise InvalidRequestException(
            f"Duplicate answers found for {raw_data.moduleId} module"
        )

    def get_validation_schema(self):
        return read_json_file(self.validation_schema_path, Path(__file__).parent)

    def calculate(self, primitive: Questionnaire):
        calculator = self._get_calculator()
        if calculator:
            calculator.calculate(primitive, self.config)

    def find_config(self, configs: Iterator[ModuleConfig], primitive: Primitive):
        def filter_config(config):
            if not isinstance(primitive, Questionnaire):
                return True

            questionnaire_id = (config.configBody or {}).get("id")
            return questionnaire_id == primitive.questionnaireId

        return super().find_config(filter(filter_config, configs), primitive)

    def filter_results(
        self,
        primitives: list[Primitive],
        module_configs: list[ModuleConfig],
        is_for_user=False,
    ) -> list[Primitive]:
        primitives = super(QuestionnaireModule, self).filter_results(
            primitives, module_configs, is_for_user
        )
        if not is_for_user:
            return primitives

        skip_ids = []
        for module_config in module_configs:
            questionnaire_id = module_config.get_config_body().get("id", None)
            if module_config.is_for_manager() and questionnaire_id:
                skip_ids.append(questionnaire_id)

        if skip_ids:
            return list(
                filter(
                    lambda x: getattr(x, "questionnaireId", None) not in skip_ids,
                    primitives,
                )
            )

        return list(filter(lambda x: not getattr(x, "isForManager", False), primitives))

    def validate_config_body(self, module_config: ModuleConfig):
        super(QuestionnaireModule, self).validate_config_body(module_config)
        for page in module_config.configBody.get("pages"):
            if page.get("type") == PageType.INFO.value:
                self._validate_info_page(page)
            # Skipping page validation due to lack of items as there can be a page without items
            items = page.get("items")
            if items is None:
                continue

            for item in items:
                if short_code := item.get("exportShortCode"):
                    self._validate_export_short_code(short_code)
                if item.get("format") == "TEXTCHOICE":
                    self._validate_text_choice(item)

    def _validate_info_page(self, info_page: dict):
        media_list = info_page.get(QuestionConfig.MEDIA) or []
        for media_id in media_list:
            if not validate_object_id(media_id):
                msg = f"Invalid media id {media_id} found in questionnaire info page"
                raise InvalidRequestException(msg)

    @staticmethod
    def _validate_export_short_code(short_code: str):
        from extensions.deployment.service.deployment_service import DeploymentService

        service = DeploymentService()
        field_path = "configBody.pages.items.exportShortCode"
        if service.check_field_value_exists_in_module_config(field_path, short_code):
            raise ConvertibleClassValidationError(
                f"Field 'exportShortCode' with value '{short_code}' already exists in system"
            )

    @staticmethod
    def _validate_text_choice(text_choice: dict):
        if not (options := text_choice.get("options")):
            raise ConvertibleClassValidationError(
                f"options for '{text_choice.get('text')} should be provided'"
            )
        for option in options:
            option_value = option.get("value")

            if not isinstance(option_value, str):
                raise ConvertibleClassValidationError(
                    f"option with value '{option_value}' for '{text_choice.get('text')} should be a string'"
                )

            if re.search(r",(?!\s)", option_value):
                raise ConvertibleClassValidationError(
                    f"Found comma followed by non-whitespace character in '{option_value}' option value for '{text_choice.get('text')}'"
                )

    def _get_calculator(self) -> Optional[QuestionnaireCalculator]:
        if self.calculator:
            return self.calculator()

        factory = QuestionnaireCalculatorFactory
        return factory.retrieve_calculator(self.config)

    @staticmethod
    def _get_option_by_name(name: str, options: list[dict]):
        return next(filter(lambda x: x["label"] == name, options), None)

    def _get_answer_weight(self, question: dict, answer: QuestionnaireAnswer):
        options = question.get("options", [])
        option = self._get_option_by_name(answer.answerText, options)
        if not option:
            msg = f"Answer {answer.answerText} is not an option"
            raise InvalidRequestException(msg)

        if "value" not in option:
            msg = f"The question {answer.questionId} doesn't have answer options configured with value"
            raise InvalidRequestException(msg)

        return option.get("weight")

    def filter_scoring_answers(
        self, answers: list[QuestionnaireAnswer], question_map: dict[str, dict] = None
    ) -> list[QuestionnaireAnswer]:
        """Return a list of answers, which doesn't have `skipCalculation` in related config"""
        if not question_map:
            question_map = config_body_to_question_map(self.config.configBody)
        return [
            answer
            for answer in answers
            if not question_map.get(answer.questionId).get("skipCalculation")
        ]

    def _preprocess_questionnaire_answers(self, answers: list[QuestionnaireAnswer]):
        multiple_choice_answers = filter(
            self._is_multiple_choice_questionnaire_answer, answers
        )
        for answer in multiple_choice_answers:
            self._preprocess_multiple_choice_question_answers(answer)

    @staticmethod
    def _is_multiple_choice_questionnaire_answer(answer: QuestionnaireAnswer):
        return (
            answer.format == QuestionAnswerFormat.TEXTCHOICE
            and answer.selectionCriteria == QuestionAnswerSelectionCriteria.MULTIPLE
        )

    @staticmethod
    def _preprocess_multiple_choice_question_answers(answer: QuestionnaireAnswer):
        if answer.otherText:
            answer.otherSelectedChoices = list(
                filter(
                    lambda text: text,
                    map(str.strip, re.split(r",|،", answer.otherText)),
                )
            )
