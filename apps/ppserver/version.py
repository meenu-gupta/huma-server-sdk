import os

__VERSION__ = "1.23.0"
__API_VERSION__ = "V1"
__BUILD__ = os.environ.get("GIT_COMMIT")
__BRANCH__ = os.environ.get("GIT_BRANCH")
