import functools
from typing import Optional

from flask import g

from extensions.deployment.models.deployment import Deployment


def enable_if_configured_or_404(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not is_summary_reports_enabled_for_deployment(g.authz_path_user.deployment):
            return "<h1>Feature is not enabled</h1>", 404
        return f(*args, **kwargs)

    return wrapper


def is_summary_reports_enabled_for_deployment(deployment: Optional[Deployment]):
    return bool(
        deployment
        and deployment.features
        and deployment.features.summaryReport
        and deployment.features.summaryReport.enabled
    )
