from sdk.auth.model.auth_user import AuthUser
from sdk.auth.repository.auth_repository import AuthRepository
from sdk.common.exceptions.exceptions import (
    InvalidUsernameOrPasswordException,
    AlreadyUsedPasswordException,
)
from sdk.common.utils.hash_utils import hash_new_password, is_correct_password
from sdk.common.utils.inject import autoparams


def get_user(repo, email=None, phone_number=None, uid=None):
    user = repo.get_user(email=email, phone_number=phone_number, uid=uid)
    if user.status != AuthUser.Status.NORMAL:
        raise InvalidUsernameOrPasswordException

    return user


@autoparams("auth_repo")
def update_password(new_password: str, email: str, auth_repo: AuthRepository):
    user = get_user(auth_repo, email=email)

    old_passwords = user.previousPasswords or []
    if current_password := user.hashedPassword:
        old_passwords.append(current_password)
    for password_hash in old_passwords[-3:]:
        if is_correct_password(password_hash, new_password):
            raise AlreadyUsedPasswordException

    new_password = hash_new_password(new_password)
    auth_repo.change_password(
        email=email, password=new_password, previous_passwords=old_passwords
    )
