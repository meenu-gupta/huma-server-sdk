from flasgger import Swagger
from flask import Flask

from sdk.limiter.config.limiter import ServerLimiterConfig
from sdk.limiter.rate_limiter import RateLimiter
from sdk.phoenix.config.server_config import SwaggerConfig


def configure_rate_limit(app: Flask, config: ServerLimiterConfig):
    default_limiter = RateLimiter(
        app,
        default_limit=config.default,
        storage_uri=config.storageUri,
    )
    return default_limiter


def configure_swagger(app, config: SwaggerConfig, api_specs):
    template = {
        "swagger": "2.0",
        "headers": [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
            ("Access-Control-Allow-Credentials", "true"),
        ],
        "info": {
            "title": "Huma SDK API",
            "description": "Rest API for Huma SDK APIs",
        },
        "schemes": ["http", "https"],
        "tags": [
            {
                "name": "storage",
                "description": "The storage API a.k.a object storage like s3",
            },
            {"name": "auth", "description": "The authentication API"},
        ],
    }

    if config.template:
        config_template = config.template
        config_tags = config_template.get("tags", [])
        default_tags = template.get("tags")
        tags = [*default_tags, *config_tags]
        template = config_template
        template["tags"] = tags

    specs = [
        {
            "endpoint": "apispec_all",
            "route": "/apispec_all.json",
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        },
    ]
    specs = specs + api_specs
    swagger_config = {
        "headers": [],
        "specs": specs,
        "static_url_path": "/flasgger_static",
        # "static_folder": "static",  # must be set by user
        "swagger_ui": True,
        "specs_route": config.specs_route,
    }
    return Swagger(app, template=template, config=swagger_config)
