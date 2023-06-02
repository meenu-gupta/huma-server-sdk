from mongoengine import (
    ObjectIdField,
    DateTimeField,
    StringField,
    DateField,
    BooleanField,
    FloatField,
    DictField,
    IntField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)

from extensions.authorization.models.user import User, BoardingStatus, PersonalDocument
from sdk.common.common_models.mongo_models import MongoS3Object
from sdk.common.utils.enum_utils import enum_values
from sdk.common.utils.mongo_utils import MongoPhoenixDocument


class MongoAddressObject(EmbeddedDocument):
    fiat_number = StringField()
    building_number = StringField()
    building_name = StringField()
    street = StringField()
    sub_street = StringField()
    town = StringField()
    state = StringField()
    postcode = StringField()
    country = StringField()
    line1 = StringField()
    line2 = StringField()
    line3 = StringField()


class MongoAdditionalContactDetails(EmbeddedDocument):
    altContactNumber = StringField()
    regularContactName = StringField()
    regularContactNumber = StringField()
    emergencyContactName = StringField()
    emergencyContactNumber = StringField()


class MongoPersonalDocument(EmbeddedDocument):
    name = StringField()
    fileType = StringField(
        choices=enum_values(PersonalDocument.PersonalDocumentMediaType)
    )
    fileObject = EmbeddedDocumentField(MongoS3Object)
    createDateTime = DateTimeField()
    updateDateTime = DateTimeField()


class MongoUserSurgeryDetails(EmbeddedDocument):
    operationType = StringField()
    implantType = StringField()
    roboticAssistance = StringField()


class MongoRoleAssignment(EmbeddedDocument):
    roleId: str = StringField()
    resource: str = StringField()
    userType: str = StringField()


class MongoTaskCompliance(EmbeddedDocument):
    current = IntField()
    total = IntField()
    due = IntField()
    updateDateTime = DateTimeField()


class MongoUserStats(EmbeddedDocument):
    taskCompliance = EmbeddedDocumentField(MongoTaskCompliance)


class MongoUser(MongoPhoenixDocument):
    meta = {"collection": "user"}

    updateDateTime = DateTimeField()
    createDateTime = DateTimeField()
    lastSubmitDateTime = DateTimeField()
    inviterId = ObjectIdField()
    givenName = StringField()
    familyName = StringField()
    gender = StringField(choices=enum_values(User.Gender))
    biologicalSex = StringField(choices=enum_values(User.BiologicalSex))
    ethnicity = StringField(choices=enum_values(User.Ethnicity))
    dateOfBirth = DateField()
    email = StringField()
    phoneNumber = StringField()

    primaryAddress = StringField()
    race = StringField()
    bloodGroup = StringField()
    emergencyPhoneNumber = StringField()
    height: float = FloatField()
    additionalContactDetails = EmbeddedDocumentField(MongoAdditionalContactDetails)
    familyMedicalHistory = StringField()
    pastHistory = StringField()
    presentSymptoms = StringField()
    operationHistory = StringField()
    chronicIllness = StringField()
    allergyHistory = StringField()
    pregnancy = StringField()
    dateOfLastPhysicalExam = DateField()
    extraCustomFields = DictField(default=None)
    surgeryDetails = EmbeddedDocumentField(MongoUserSurgeryDetails)
    # extra IDs
    fenlandCohortId = StringField()
    nhsId = StringField()
    insuranceNumber = StringField()
    wechatId = StringField()
    kardiaId = StringField()
    pamThirdPartyIdentifier = StringField()

    roles = EmbeddedDocumentListField(MongoRoleAssignment)
    timezone = StringField()
    recentModuleResults: dict = DictField(default=None)
    tags: dict = DictField(default=None)
    tagsAuthorId: str = ObjectIdField()
    surgeryDateTime = DateTimeField()
    carePlanGroupId = StringField()
    preferredUnits: dict = DictField(default=None)
    addressComponent = EmbeddedDocumentField(MongoAddressObject)
    onfidoApplicantId = StringField()
    verificationStatus = IntField(choices=enum_values(User.VerificationStatus))
    personalDocuments = EmbeddedDocumentListField(MongoPersonalDocument)
    enrollmentId: int = IntField()
    boardingStatus = IntField(choices=BoardingStatus)
    language = StringField()
    lastLoginDateTime = DateTimeField()
    finishedOnboarding: bool = BooleanField()
    stats = EmbeddedDocumentField(MongoUserStats)
