from extensions.authorization.models.authorized_user import AuthorizedUser


def is_user_proxy_or_user_type(authz_user: AuthorizedUser):
    return authz_user.is_user() or authz_user.is_proxy()
