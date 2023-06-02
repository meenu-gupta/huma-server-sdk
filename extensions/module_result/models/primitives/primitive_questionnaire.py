"""model for questionnaire result object"""
from enum import Enum
from typing import Any

from sdk import meta, convertibleclass
from sdk.common.utils.convertible import required_field, default_field
from sdk.common.utils.validators import (
    must_be_at_least_one_of,
    validate_len,
    validate_list_elements_len,
    must_be_present,
    validate_object_id,
    not_empty,
)
from .primitive import Primitive


class PageType(Enum):
    QUESTION = "QUESTION"
    INFO = "INFO"


class QuestionnaireAnswerMediaType(Enum):
    PHOTO = "PHOTO"
    FILE = "FILE"
    VIDEO = "VIDEO"


@convertibleclass
class QuestionnaireAnswerMediaFile:
    FILE = "file"
    THUMBNAIL = "thumbnail"
    MEDIA_TYPE = "mediaType"

    file: str = required_field(metadata=meta(validate_object_id))
    thumbnail: str = default_field(metadata=meta(validate_object_id))
    mediaType: QuestionnaireAnswerMediaType = required_field(metadata=meta(not_empty))


class QuestionAnswerFormat(Enum):
    NUMERIC = "NUMERIC"
    NUMERIC_UNIT = "NUMERIC_UNIT"
    TEXTCHOICE = "TEXTCHOICE"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TEXT = "TEXT"
    DURATION = "DURATION"
    DURATION_SECONDS = "DURATION_SECONDS"
    SCALE = "SCALE"
    COMPOSITE = "COMPOSITE"
    LIST = "LIST"
    MEDIA = "MEDIA"
    AUTOCOMPLETE_TEXT = "AUTOCOMPLETE_TEXT"

    @classmethod
    def _missing_(cls, value):
        """This method is to support backward compatibility for TEXT_CHOICE"""
        if value == "TEXT_CHOICE":
            return QuestionAnswerFormat.TEXTCHOICE


class QuestionConfig:
    LOWER_BOUND = "lowerBound"
    UPPER_BOUND = "upperBound"
    ALLOW_INTEGERS_ONLY = "allowsIntegersOnly"
    FORMAT = "format"
    SKIP_BY_WEIGHT = "skipByWeight"
    MAX_DECIMALS = "maxDecimals"
    MULTIPLE_ANSWERS = "multipleAnswers"
    MAX_ANSWERS = "maxAnswers"
    ENABLED = "enabled"
    MEDIA_TYPE = "mediaType"
    AUTOCOMPLETE = "autocomplete"
    OPTIONS = "options"
    KEY = "key"
    VALUE = "value"
    MEDIA = "media"


class QuestionAnswerSelectionCriteria(Enum):
    MULTIPLE = "MULTIPLE"
    FIELD = "FIELD"
    SINGLE = "SINGLE"


@convertibleclass
class QuestionnaireAnswer:
    """Questionnaire Answer model"""

    QUESTION = "question"
    ANSWER_TEXT = "answerText"
    ANSWERS_LIST = "answersList"
    FILES_LIST = "filesList"
    OTHER_TEXT = "otherText"
    COMPOSITE_ANSWER = "compositeAnswer"
    CHOICES = "choices"
    QUESTION_ID = "questionId"
    ANSWER_SCORE = "answerScore"
    ANSWER_CHOICES = "answerChoices"
    FORMAT = "format"
    SELECTION_CRITERIA = "selectionCriteria"
    SELECTED_CHOICES = "selectedChoices"
    OTHER_SELECTED_CHOICES = "otherSelectedChoices"
    VALUE = "value"
    UPPER_BOUND = "upperBound"
    LOWER_BOUND = "lowerBound"
    UNITS = "units"
    SELECTED_UNIT = "selectedUnit"
    RECALLED_TEXT = "recalledText"

    answerText: str = default_field()
    answersList: list[str] = default_field()
    filesList: list[QuestionnaireAnswerMediaFile] = default_field()
    otherText: str = default_field()
    value: Any = default_field()
    compositeAnswer: dict = default_field()
    # answerScore is always calculated within the backend
    answerScore: int = default_field()
    questionId: str = default_field()
    question: str = required_field()
    format: QuestionAnswerFormat = default_field()
    choices: list[str] = default_field()
    selectedChoices: list[str] = default_field()
    otherSelectedChoices: list[str] = default_field()
    selectionCriteria: QuestionAnswerSelectionCriteria = default_field()
    lowerBound: float = default_field(metadata=meta(value_to_field=float))
    upperBound: float = default_field(metadata=meta(value_to_field=float))
    lists: list[str] = default_field()
    units: list[str] = default_field(metadata=meta(validate_list_elements_len(max=10)))
    selectedUnit: str = default_field()
    recalledText: list[str] = default_field()

    @classmethod
    def validate(cls, answer: "QuestionnaireAnswer"):
        # no validation as a fix for Android < 1.15
        # TODO: make incompatible apps to do force update to the latest version
        if answer:
            return

        if answer.format == QuestionAnswerFormat.TEXT:
            must_be_present(answerText=answer.answerText)
        elif answer.format == QuestionAnswerFormat.COMPOSITE:
            must_be_present(compositeAnswer=answer.compositeAnswer)
        elif answer.format == QuestionAnswerFormat.BOOLEAN:
            must_be_present(value=answer.value)
        elif answer.format == QuestionAnswerFormat.LIST:
            must_be_present(value=answer.lists)
        elif answer.format == QuestionAnswerFormat.TEXTCHOICE:
            cls._validate_text_choice(answer)
        elif answer.format == QuestionAnswerFormat.SCALE:
            must_be_present(
                value=answer.value,
                upperBound=answer.upperBound,
                lowerBound=answer.lowerBound,
            )
        else:
            must_be_at_least_one_of(
                answerText=answer.answerText,
                compositeAnswer=answer.compositeAnswer,
            )

    @staticmethod
    def _validate_text_choice(answer: "QuestionnaireAnswer"):
        must_be_present(
            choices=answer.choices,
            selectedChoices=answer.selectedChoices,
            selectionCriteria=answer.selectionCriteria,
        )

        if answer.must_contain_only_one_choice():
            number_of_choices = len(answer.selectedChoices)
            if number_of_choices > 1:
                raise Exception(
                    f"Only one choice is allowed for question [{answer.questionId}]"
                )

    def must_contain_only_one_choice(self):
        return self.selectionCriteria == QuestionAnswerSelectionCriteria.SINGLE

    def get_answer(self):
        if self.format == QuestionAnswerFormat.COMPOSITE:
            return self.compositeAnswer
        elif self.format == QuestionAnswerFormat.BOOLEAN:
            return self.value
        elif self.format == QuestionAnswerFormat.LIST:
            return self.value
        elif self.format == QuestionAnswerFormat.TEXTCHOICE:
            return self.selectedChoices
        elif self.format == QuestionAnswerFormat.SCALE:
            return self.value
        else:
            return self.compositeAnswer or self.answerText


class SkippedQuestionnaireAnswer(QuestionnaireAnswer):
    @classmethod
    def validate(cls, answer: "SkippedQuestionnaireAnswer"):
        pass


@convertibleclass
class QuestionnaireMetadata:
    ANSWERS = "answers"

    answers: list[QuestionnaireAnswer] = required_field()


@convertibleclass
class QuestionnaireAppResultValue:
    """Questionnaire results that are calculated by the app, not the backend"""

    class QuestionnaireAppResultValueType(Enum):
        VALUE_FLOAT = "VALUE_FLOAT"
        STD_ERR_FLOAT = "STD_ERR_FLOAT"

    LABEL = "label"
    VALUE_TYPE = "valueType"
    VALUE_FLOAT = "valueFloat"

    label: str = required_field(metadata=meta(validate_len(1, 63)))
    valueType: QuestionnaireAppResultValueType = required_field()
    # As different valueTypes are added only one of (e.g. valueFloat, valueInt, ...)
    # will be required. When that happens don't forget to make them all required-False
    # and add a validator that ensures one and only one is provided.

    # No validation ... it's an opaque value since backend don't own the computation
    valueFloat: float = required_field(metadata=meta(value_to_field=float))


@convertibleclass
class QuestionnaireAppResult:
    class QuestionnaireAppResultType(Enum):
        T_DISTRIBUTION = "T_DISTRIBUTION"
        GRADED_RESULT = "GRADED_RESULT"

    APP_TYPE = "appType"
    VALUES = "values"

    appType: QuestionnaireAppResultType = required_field()
    values: list[QuestionnaireAppResultValue] = required_field()


@convertibleclass
class Questionnaire(Primitive):
    """Questionnaire model"""

    ANSWERS = "answers"
    QUESTIONNAIRE_ID = "questionnaireId"
    QUESTIONNAIRE_NAME = "questionnaireName"
    VALUE = "value"
    SKIPPED = "skipped"

    answers: list[QuestionnaireAnswer] = required_field()
    appResult: QuestionnaireAppResult = default_field()
    isForManager: bool = default_field()
    # questionnaireId is the id of the ModuleConfig that contains this questionnaire
    questionnaireId: str = required_field()
    questionnaireName: str = required_field()
    # value is calculated within the backend, whenever any question has a score
    value: float = default_field(metadata=meta(value_to_field=float))
    skipped: list[SkippedQuestionnaireAnswer] = default_field()
