from datetime import datetime
from mongoengine import (
    StringField,
    EmbeddedDocumentField,
    DateTimeField,
    ListField,
    BooleanField,
    IntField,
    DictField,
    ObjectIdField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)

from extensions.authorization.repository.models.mongo_role_model import MongoRole
from extensions.deployment.models.deployment import AppMenuItem
from extensions.deployment.models.learn import LearnArticleType, LearnArticleContentType
from extensions.deployment.models.status import Status, EnableStatus
from extensions.deployment.repository.models.mongo_care_plan_group_model import (
    MongoCarePlanGroup,
)
from extensions.deployment.repository.models.mongo_consent_model import MongoConsent
from extensions.deployment.repository.models.mongo_econsent_model import MongoEConsent
from extensions.deployment.repository.models.mongo_key_action_config_model import (
    MongoKeyActionConfig,
)
from extensions.deployment.repository.models.mongo_module_config_model import (
    MongoModuleConfig,
)
from extensions.deployment.repository.models.mongo_profile_model import MongoProfile
from extensions.deployment.repository.models.mongo_stats_model import (
    MongoDeploymentStats,
)
from extensions.identity_verification.models.identity_verification import (
    OnfidoReportNameType,
)
from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoOnboardingModuleConfig(EmbeddedDocument):
    id = ObjectIdField()
    onboardingId = StringField()
    status = StringField(choices=enum_values(EnableStatus))
    configBody = DictField()
    order = IntField()
    version = IntField()
    userTypes = ListField(StringField())


class MongoLearnArticleContent(EmbeddedDocument):
    id = ObjectIdField()
    type = StringField(choices=enum_values(LearnArticleContentType))
    timeToRead = StringField()
    textDetails = StringField()
    videoUrl = EmbeddedDocumentField(MongoS3Object)
    url = StringField()


class MongoLearnArticle(EmbeddedDocument):
    id = ObjectIdField()
    title = StringField()
    type = StringField(choices=enum_values(LearnArticleType))
    thumbnailUrl = EmbeddedDocumentField(MongoS3Object)
    order = IntField()
    content = EmbeddedDocumentField(MongoLearnArticleContent)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()


class MongoLearnSection(EmbeddedDocument):
    id = ObjectIdField()
    title = StringField()
    order = IntField()
    articles = EmbeddedDocumentListField(MongoLearnArticle)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()


class MongoLearn(EmbeddedDocument):
    id = ObjectIdField()
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    sections = EmbeddedDocumentListField(MongoLearnSection)


class MongoMessaging(EmbeddedDocument):
    enabled = BooleanField()
    messages = ListField(StringField())


class MongoSurgeryDateRule(EmbeddedDocument):
    maxPastRange = StringField()
    maxFutureRange = StringField()


class MongoReason(EmbeddedDocument):
    order = IntField(min_value=1, max_value=100)
    displayName = StringField(max_length=256)


class MongoOffBoardingReasons(EmbeddedDocument):
    reasons = EmbeddedDocumentListField(MongoReason)
    otherReason = BooleanField(default=True)


class MongoLabel(EmbeddedDocument):
    id = ObjectIdField()
    text = StringField()
    authorId = StringField()
    createDateTime = DateTimeField(default=datetime.now())
    updateDateTime = DateTimeField()


class MongoFeatures(EmbeddedDocument):
    appMenu = ListField(StringField(choices=enum_values(AppMenuItem)))
    appointment = BooleanField()
    carePlanDailyAdherence = BooleanField()
    healthDeviceIntegration = BooleanField()
    labels = BooleanField()
    offBoarding = BooleanField()
    offBoardingReasons = EmbeddedDocumentField(MongoOffBoardingReasons)
    personalDocuments = BooleanField()
    proxy = BooleanField()
    surgeryDateRule = EmbeddedDocumentField(MongoSurgeryDateRule)
    portal = DictField()
    messaging = EmbeddedDocumentField(MongoSurgeryDateRule)
    hideAppSupport = BooleanField()
    linkInvites = BooleanField()
    personalizedConfig = BooleanField()


class MongoSurgeryDetailItem(EmbeddedDocument):
    key = StringField()
    value = StringField()
    order = IntField()


class MongoSurgeryDetail(EmbeddedDocument):
    displayString = StringField()
    placeHolder = StringField()
    order = IntField()
    items = EmbeddedDocumentListField(MongoSurgeryDetailItem)


class MongoSurgeryDetails(EmbeddedDocument):
    operationType = EmbeddedDocumentField(MongoSurgeryDetail)
    implantType = EmbeddedDocumentField(MongoSurgeryDetail)
    roboticAssistance = EmbeddedDocumentField(MongoSurgeryDetail)


class MongoPAMIntegrationConfig(EmbeddedDocument):
    submitSurveyURI = StringField()
    enrollUserURI = StringField()
    clientExtID = StringField()
    clientPassKeyEncrypted = StringField()
    subgroupExtID = StringField()


class MongoIntegrationConfig(EmbeddedDocument):
    pamConfig = EmbeddedDocumentField(MongoPAMIntegrationConfig)


class MongoStaticEventConfig(EmbeddedDocument):
    title = StringField()
    description = StringField()


class MongoBaseDeployment:
    name = StringField()
    description = StringField()
    status = StringField(choices=enum_values(Status))
    color = StringField()
    icon = EmbeddedDocumentField(MongoS3Object)
    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    userActivationCode = StringField()
    managerActivationCode = StringField()
    proxyActivationCode = StringField()
    moduleConfigs = EmbeddedDocumentListField(MongoModuleConfig, default=None)
    onboardingConfigs = EmbeddedDocumentListField(
        MongoOnboardingModuleConfig, default=None
    )
    learn = EmbeddedDocumentField(MongoLearn)
    consent = EmbeddedDocumentField(MongoConsent)
    econsent = EmbeddedDocumentField(MongoEConsent)
    keyActions = EmbeddedDocumentListField(MongoKeyActionConfig, default=None)
    keyActionsEnabled = BooleanField()
    profile = EmbeddedDocumentField(MongoProfile)
    features = EmbeddedDocumentField(MongoFeatures)
    extraCustomFields = DictField(default=None)
    surgeryDetails = EmbeddedDocumentField(MongoSurgeryDetails)
    privacyPolicyUrl = StringField()
    eulaUrl = StringField()
    contactUsURL = StringField()
    termAndConditionUrl = StringField()
    version = IntField()
    integration = EmbeddedDocumentField(MongoIntegrationConfig)
    carePlanGroup = EmbeddedDocumentField(MongoCarePlanGroup)
    language = StringField()
    roles = EmbeddedDocumentListField(MongoRole, default=None)
    duration = StringField()
    mfaRequired = BooleanField()
    code = StringField()
    enrollmentCounter = IntField()
    staticEventConfig = EmbeddedDocumentField(MongoStaticEventConfig)
    onfidoRequiredReports = ListField(
        StringField(choices=enum_values(OnfidoReportNameType)), default=None
    )
    stats = EmbeddedDocumentField(MongoDeploymentStats)
    localizations = DictField(default=None)
    country = StringField()
    labels = EmbeddedDocumentListField(MongoLabel)


class MongoDeployment(MongoPhoenixDocument, MongoBaseDeployment):
    meta = {"collection": "deployment"}


class MongoEmbeddedDeployment(EmbeddedDocument, MongoBaseDeployment):
    pass
