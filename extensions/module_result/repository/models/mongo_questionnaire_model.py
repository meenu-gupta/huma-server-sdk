from mongoengine import (
    ObjectIdField,
    StringField,
    BooleanField,
    FloatField,
    DictField,
    ListField,
    IntField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    DynamicField,
    EmbeddedDocumentListField,
)

from extensions.module_result.models.primitives.primitive_questionnaire import (
    QuestionAnswerFormat,
    QuestionAnswerSelectionCriteria,
    QuestionnaireAppResultValue,
    QuestionnaireAppResult,
)
from extensions.module_result.repository.models import MongoPrimitive
from sdk.common.utils.enum_utils import enum_values


class MongoQuestionnaireAnswer(EmbeddedDocument):
    id = ObjectIdField()
    answerText = StringField()
    value = DynamicField()
    compositeAnswer = DictField()
    answerScore = IntField()
    questionId = StringField()
    question = StringField()
    format = StringField(choices=enum_values(QuestionAnswerFormat))
    choices = ListField(StringField())
    selectedChoices = ListField(StringField())
    selectionCriteria = StringField(
        choices=enum_values(QuestionAnswerSelectionCriteria)
    )
    lowerBound = IntField()
    upperBound = IntField()
    lists = ListField(StringField())


class MongoQuestionnaireAppResultValue(EmbeddedDocument):
    id = ObjectIdField()
    label = StringField()
    valueType = StringField(
        choices=enum_values(QuestionnaireAppResultValue.QuestionnaireAppResultValueType)
    )
    valueFloat = FloatField()


class MongoQuestionnaireAppResult(EmbeddedDocument):
    id = ObjectIdField()
    appType = StringField(
        choices=enum_values(QuestionnaireAppResult.QuestionnaireAppResultType)
    )
    values = EmbeddedDocumentListField(MongoQuestionnaireAppResultValue)


class MongoQuestionnaire(MongoPrimitive):
    meta = {"collection": "questionnaire"}

    answers = EmbeddedDocumentListField(MongoQuestionnaireAnswer)
    appResult = EmbeddedDocumentField(MongoQuestionnaireAppResult)
    isForManager = BooleanField()
    questionnaireId = StringField()
    questionnaireName = StringField()
    value = FloatField()
    skipped = EmbeddedDocumentListField(MongoQuestionnaireAnswer)
