from urllib.parse import urlparse


def clean_password_from_url(url):
    parsed = urlparse(url)
    replaced = parsed._replace(
        netloc="{}:{}@{}".format(parsed.username, "???", parsed.hostname)
    )
    return replaced.geturl()
