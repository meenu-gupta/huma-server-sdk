from mongoengine import (
    EmbeddedDocumentField,
    EmbeddedDocument,
    BooleanField,
    DictField,
    ListField,
    StringField,
    EmbeddedDocumentListField,
)


class MongoAdditionalContactDetailsItem(EmbeddedDocument):
    altContactNumber = BooleanField()
    regularContactName = BooleanField()
    regularContactNumber = BooleanField()
    emergencyContactName = BooleanField()
    emergencyContactNumber = BooleanField()
    mandatoryFields = ListField(StringField())


class MongoEthnicityOption(EmbeddedDocument):
    displayName = StringField()
    value = StringField()


class MongoGenderOptionType(EmbeddedDocument):
    displayName = StringField()
    value = StringField()


class MongoProfileExtraIds(EmbeddedDocument):
    fenlandCohortId = BooleanField()
    nhsId = BooleanField()
    insuranceNumber = BooleanField()
    wechatId = BooleanField()
    aliveCorId = BooleanField()

    mandatoryOnboardingIds = ListField(StringField())
    unEditableIds = ListField(StringField())


class MongoProfileFields(EmbeddedDocument):
    givenName = BooleanField()
    familyName = BooleanField()
    dateOfBirth = BooleanField()
    race = BooleanField()
    gender = BooleanField()
    biologicalSex = BooleanField()
    genderOptions = EmbeddedDocumentListField(MongoGenderOptionType)
    bloodGroup = BooleanField()
    height = BooleanField()
    additionalContactDetails = EmbeddedDocumentField(MongoAdditionalContactDetailsItem)
    phoneNumber = BooleanField()
    email = BooleanField()
    primaryAddress = BooleanField()
    emergencyPhoneNumber = BooleanField()
    ethnicityOptions = EmbeddedDocumentListField(MongoEthnicityOption)
    ethnicity = BooleanField()
    familyMedicalHistory = BooleanField()
    pastHistory = BooleanField()
    presentSymptoms = BooleanField()
    operationHistory = BooleanField()
    chronicIllness = BooleanField()
    allergyHistory = BooleanField()
    pregnancy = BooleanField()
    dateOfLastPhysicalExam = BooleanField()
    extraIds = EmbeddedDocumentField(MongoProfileExtraIds)
    mandatoryOnboardingFields = ListField(StringField())
    unEditableFields = ListField(StringField())
    validators = DictField()


class MongoClinicianOnlyFields(EmbeddedDocument):
    surgeryDateTime = BooleanField()


class MongoProfile(EmbeddedDocument):
    fields = EmbeddedDocumentField(MongoProfileFields)
    clinicianOnlyFields = EmbeddedDocumentField(MongoClinicianOnlyFields)
