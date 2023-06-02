import os

__VERSION__ = "1.1.0-beta"
__API_VERSION__ = "V1"
__BUILD__ = os.environ.get("GIT_COMMIT")
__BRANCH__ = os.environ.get("GIT_BRANCH")
