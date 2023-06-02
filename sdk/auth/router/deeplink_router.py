import os

import i18n
from flask import (
    Blueprint,
    jsonify,
    Flask,
    make_response,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)

from sdk.auth.use_case.auth_use_cases import (
    RetrieveDeepLinkAndroidAppUseCase,
    RetrieveDeepLinkAppleAppUseCase,
)
from sdk.common.localization.utils import Language
from sdk.common.usecase.request_object import RequestObject
from sdk.common.utils.inject import autoparams
from sdk.phoenix.config.server_config import PhoenixServerConfig

deeplink_api = Blueprint(
    "deeplink_route",
    __name__,
)

app = Flask(__name__, template_folder="templates/")


@deeplink_api.route("/.well-known/apple-app-site-association", methods=["GET"])
def retrieve_deeplink_for_apple_app():
    """
    This is used by apple CDN to redirect deeplink to ios app. So no docs needed
    """
    return (
        jsonify(RetrieveDeepLinkAppleAppUseCase().execute(RequestObject()).value),
        200,
    )


@deeplink_api.route("/.well-known/assetlinks.json", methods=["GET"])
def retrieve_deeplink_for_android_app():
    """
    This is used by android CDN to redirect deeplink to android app. So no docs needed
    """
    return (
        jsonify(RetrieveDeepLinkAndroidAppUseCase().execute(RequestObject())),
        200,
    )


@deeplink_api.route("/install-app", methods=["GET"])
@autoparams()
def install_app_html_page(config: PhoenixServerConfig):
    headers = {"Content-Type": "text/html"}
    locale = Language.EN
    title = i18n.t("InstallApp.title", locale=locale)
    description = i18n.t("InstallApp.description", locale=locale)
    app_store_link = config.server.iosAppUrl
    google_play_link = config.server.androidAppUrl
    params = {
        "title": title,
        "description": description,
        "appStoreLink": app_store_link,
        "googlePlayLink": google_play_link,
    }
    with app.app_context():
        return make_response(
            render_template("install_app.html", **params),
            200,
            headers,
        )


@deeplink_api.route("/signup", methods=["GET"])
def signup_html_page():
    return redirect(url_for("deeplink_route.install_app_html_page"))


@deeplink_api.route("/register", methods=["GET"])
def register_html_page():
    return redirect(url_for("deeplink_route.install_app_html_page"))


@deeplink_api.route("/login", methods=["GET"])
def login_html_page():
    return redirect(url_for("deeplink_route.install_app_html_page"))


@deeplink_api.route("/reset-password", methods=["GET"])
def reset_password_html_page():
    return redirect(url_for("deeplink_route.install_app_html_page"))


@deeplink_api.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "images"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
