import requests


def minio_is_ready(minio_url: str):
    rsp = requests.get("http://" + minio_url + "/minio/health/ready")
    if rsp.status_code >= 400:
        return False

    return True
