from flask import g, has_request_context, Flask

from sdk.common.monitoring.monitoring import report_exception as report

app = Flask(__name__)


def report_exception(
    error,
    context_name: str = None,
    context_content: dict = None,
    tags: dict[str, str] = None,
):
    tags = tags or {}

    if has_request_context():
        if g.get("authz_user"):
            from extensions.authorization.models.authorized_user import AuthorizedUser

            tags = {
                AuthorizedUser.DEPLOYMENT_ID: g.authz_user.deployment_id(),
                AuthorizedUser.ORGANIZATION_ID: g.authz_user.organization_id(),
                AuthorizedUser.USER_TYPE: g.authz_user.user_type(),
                **tags,
            }
        report(error, context_name, context_content, tags)
    else:
        with app.app_context():
            report(error, context_name, context_content, tags)
