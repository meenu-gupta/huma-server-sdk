from enum import Enum


class AuthorizationAction(Enum):
    SendInvitation = "SendInvitation"
    ResendBulkEmailInvitation = "ResendBulkEmailInvitation"
    SendAdminInvitation = "SendAdminInvitation"
    DeleteInvitation = "DeleteInvitation"
    DeleteBulkInvitation = "DeleteBulkInvitation"
    GetInvitationLink = "GetInvitationLink"

    CreateUser = "CreateUser"
    UpdateUser = "UpdateUser"
    DeleteUser = "DeleteUser"
    OffBoardUser = "OffBoardUser"
    OffBoardUsers = "OffBoardUsers"
    ReactivateUser = "ReactivateUser"
    ReactivateUsers = "ReactivateUsers"

    AssignLabelsToUser = "AssignLabelsToUser"
    AssignLabelsToUsers = "AssignLabelsToUsers"

    CreateTag = "CreateTag"
    DeleteTag = "DeleteTag"

    SignConsent = "SignConsent"
    SignEConsent = "SignEConsent"

    LinkProxyUser = "LinkProxyUser"
    UnLinkProxyUser = "UnLinkProxyUser"

    CreatePersonalDocument = "CreatePersonalDocument"
    CreateHelperAgreementLog = "CreateHelperAgreementLog"
    UpdateUserCarePlanGroup = "UpdateUserCarePlanGroup"
    AssignManager = "AssignManager"
    AssignManagersToUsers = "AssignManagersToUsers"

    AddRoles = "AddRoles"
    AddRolesToUsers = "AddRolesToUsers"
    RemoveRoles = "RemoveRoles"
