import re
import sys
from abc import ABC, abstractmethod
from typing import Optional

from sdk.common.exceptions.exceptions import InvalidRequestException
from extensions.module_result.models.primitives import QuestionnaireAnswer
from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
    QuestionConfig,
    QuestionAnswerSelectionCriteria,
)
from extensions.module_result.module_result_utils import config_body_to_question_map


class AnswerValidator(ABC):
    @staticmethod
    @abstractmethod
    def validate(answer: QuestionnaireAnswer, question_config: dict):
        raise NotImplementedError


class NumericAnswerValidator(AnswerValidator):
    @staticmethod
    def validate(answer: QuestionnaireAnswer, question_config: dict):
        lower_bound = question_config.get(QuestionConfig.LOWER_BOUND)
        upper_bound = question_config.get(QuestionConfig.UPPER_BOUND)
        integer_only = question_config.get(QuestionConfig.ALLOW_INTEGERS_ONLY)

        num_regex = re.compile(r"^-?[0-9]\d*(\.\d+)?$")
        if not num_regex.match(answer.answerText):
            raise InvalidRequestException(f"{answer.questionId} should be numeric")

        if integer_only and "." in answer.answerText:
            raise InvalidRequestException(f"{answer.questionId} accepts only integers")

        num_answer = float(answer.answerText)
        if lower_bound and num_answer < lower_bound:
            raise InvalidRequestException(
                f"{answer.questionId} should not be lower {lower_bound}"
            )
        if upper_bound and num_answer > upper_bound:
            raise InvalidRequestException(
                f"{answer.questionId} should not be greater {upper_bound}"
            )
        units = question_config.get(QuestionnaireAnswer.UNITS, [])
        if answer.selectedUnit and answer.selectedUnit not in units:
            raise InvalidRequestException(
                f"{answer.questionId} selected unit is not among allowed units {answer.selectedUnit}"
            )
        max_decimals = question_config.get(QuestionConfig.MAX_DECIMALS)
        if max_decimals:
            number_parts = answer.answerText.split(".")
            if number_parts == 2 and len(number_parts[1]) > max_decimals:
                raise InvalidRequestException(
                    f"{answer.questionId} number of decimals ({len(number_parts[1])}) is more than allowed maximum ({max_decimals})"
                )


class TextChoiceAnswerValidator(AnswerValidator):
    @staticmethod
    def validate(answer: QuestionnaireAnswer, question_config: dict):
        options = question_config.get("options", [])
        selected_choices = answer.selectedChoices or []
        options_values = [option.get("value") for option in options]
        for selected_choice in selected_choices:
            if selected_choice not in options_values:
                raise InvalidRequestException(
                    f"{answer.questionId} selected choice: {selected_choice} is not an option"
                )

        selection_criteria = question_config.get(QuestionnaireAnswer.SELECTION_CRITERIA)
        if selection_criteria == QuestionAnswerSelectionCriteria.MULTIPLE.value:
            for option in options:
                if option.get("exclusive"):
                    option_value = option.get("value")
                    if option_value in selected_choices and len(selected_choices) != 1:
                        raise InvalidRequestException(
                            f"{answer.questionId} invalid selected choices: exclusive choice is selected among others"
                        )
                if other := option.get("other"):
                    option_value = option.get("value")
                    if (
                        other.get("enabled")
                        and option_value in selected_choice
                        and not answer.otherText
                    ):
                        raise InvalidRequestException(
                            f"{answer.questionId} 'other' option is selected without providing otherText"
                        )
        elif selection_criteria == QuestionAnswerSelectionCriteria.SINGLE.value:
            if len(selected_choice) > 1:
                raise InvalidRequestException(
                    f"{answer.questionId} multiple choices are selected for single choice questionnaire"
                )


class MediaAnswerValidator(AnswerValidator):
    """This is a validator for Media answer types. It validates file numbers
    and media types based on the restrictions, max answer, and media type.
    If multiple_answers_config in not enabled the maximum answer will be 1.
    If it is enabled the value of maximum answer is sys.maxsize, unless
    there is a correct restriction in the answer config."""

    @staticmethod
    def validate(answer: QuestionnaireAnswer, question_config: dict):

        multiple_answers_config = question_config.get(
            QuestionConfig.MULTIPLE_ANSWERS, {}
        )
        if multiple_answers_config.get(QuestionConfig.ENABLED):
            if multiple_answers_config.get(QuestionConfig.MAX_ANSWERS):
                max_answers = multiple_answers_config.get(QuestionConfig.MAX_ANSWERS)
            else:
                max_answers = sys.maxsize
        else:
            max_answers = 1
        if max_answers <= 0:
            max_answers = sys.maxsize
        files_list = answer.filesList or []

        if len(files_list) > max_answers:
            raise InvalidRequestException(
                f"Number of files in question {answer.questionId} is greater than"
                f" max_answers: {len(files_list)} > {max_answers}"
            )

        media_type_list = question_config.get(QuestionConfig.MEDIA_TYPE, [])
        for file in files_list:
            if file.mediaType.value not in media_type_list:
                raise InvalidRequestException(
                    f"File format {file.mediaType.value} is not acceptable in question "
                    f"{answer.questionId}"
                )


class QuestionnaireAnswerValidatorFactory:
    @staticmethod
    def retrieve_validator(question_config: dict) -> Optional[AnswerValidator]:
        rules_mapping = {
            QuestionAnswerFormat.NUMERIC.value: NumericAnswerValidator,
            QuestionAnswerFormat.TEXTCHOICE.value: TextChoiceAnswerValidator,
            QuestionAnswerFormat.AUTOCOMPLETE_TEXT.value: AutoCompleteAnswerValidator,
            QuestionAnswerFormat.MEDIA.value: MediaAnswerValidator,
        }
        answer_format_name = question_config.get(QuestionConfig.FORMAT)
        return rules_mapping.get(answer_format_name)


class QuestionnaireAnswerValidator:
    factory = QuestionnaireAnswerValidatorFactory

    def __init__(self, questionnaire_config: dict):
        self._questionnaire_config = self._map_config_body(questionnaire_config)

    @staticmethod
    def _map_config_body(questionnaire_config):
        return config_body_to_question_map(questionnaire_config)

    def validate_answer(self, answer: QuestionnaireAnswer):
        if not (answer.answerText or answer.answersList or answer.filesList):
            return

        question_config = self._questionnaire_config.get(answer.questionId)
        if not question_config:
            return

        multiple_answers_config = question_config.get(
            QuestionConfig.MULTIPLE_ANSWERS, {}
        )
        if multiple_answers_config.get(QuestionConfig.ENABLED):
            self.validate_multiple_answers(answer, multiple_answers_config)

        if validation_class := self.factory.retrieve_validator(question_config):
            validation_class.validate(answer, question_config)

    @staticmethod
    def validate_multiple_answers(
        answer: QuestionnaireAnswer, multiple_answers_config: dict
    ):
        answers_list = answer.answersList or []
        max_answers = multiple_answers_config.get(QuestionConfig.MAX_ANSWERS)
        if not max_answers or max_answers <= 0:
            max_answers = sys.maxsize
        if len(answers_list) > max_answers:
            raise InvalidRequestException(
                f"Number of answers in question {answer.questionId} is greater than max_answers: {len(answers_list)} > {max_answers}"
            )


class AutoCompleteAnswerValidator(AnswerValidator):
    @staticmethod
    def validate(answer: QuestionnaireAnswer, question_config: dict):
        multiple_answers_config = question_config.get(
            QuestionConfig.MULTIPLE_ANSWERS, {}
        )
        if multiple_answers_config.get(QuestionConfig.ENABLED):
            QuestionnaireAnswerValidator.validate_multiple_answers(
                answer, multiple_answers_config
            )

        autocomplete_answers_config = question_config.get(
            QuestionConfig.AUTOCOMPLETE, {}
        )
        if autocomplete_answers_config:
            AutoCompleteAnswerValidator.validate_autocomplete_answers(
                answer, autocomplete_answers_config
            )

    @staticmethod
    def validate_autocomplete_answers(
        answer: QuestionnaireAnswer, autocomplete_config: dict
    ):
        if "options" not in autocomplete_config:
            raise InvalidRequestException(
                f"Auto complete question {answer.questionId} does not have 'options' key in its 'autocomplete' field"
            )
        autocomplete_options = autocomplete_config["options"]
        if not isinstance(autocomplete_options, list):
            raise InvalidRequestException(
                f"'options' in auto complete question {answer.questionId} should be an array"
            )
        for i, item in enumerate(autocomplete_options):
            if not isinstance(item, dict):
                raise InvalidRequestException(
                    f"'options' item {i+1} in auto complete question {answer.questionId} should be an object"
                )
            if "key" not in item or "value" not in item:
                raise InvalidRequestException(
                    f"'options' item {i+1} in auto complete question {answer.questionId} should have both 'key' and 'value'"
                )
