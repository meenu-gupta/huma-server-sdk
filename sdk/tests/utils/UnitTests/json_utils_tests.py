# -*- coding: utf-8 -*-
from sdk.common.utils.json_utils import (
    camelize,
    decamelize,
    depascalize,
    pascalize,
    is_pascalcase,
    is_snakecase,
    is_camelcase,
    replace_values,
)


def test_converting_strings():
    assert camelize("jack_in_the_box") == "jackInTheBox"
    assert decamelize("rubyTuesdays") == "ruby_tuesdays"
    assert depascalize("UnosPizza") == "unos_pizza"
    assert pascalize("red_robin") == "RedRobin"


def test_camelized_acronyms():
    assert decamelize("PERatio") == "pe_ratio"
    assert decamelize("HTTPResponse") == "http_response"
    assert decamelize("_HTTPResponse") == "_http_response"
    assert decamelize("_HTTPResponse__") == "_http_response__"
    assert decamelize("BIP73") == "BIP73"
    assert decamelize("BIP72b") == "bip72b"


def test_conditionals():
    assert is_pascalcase("RedRobin")
    assert is_snakecase("RedRobin") is False
    assert is_camelcase("RedRobin") is False

    assert is_snakecase("ruby_tuesdays")
    assert is_camelcase("ruby_tuesdays") is False
    assert is_pascalcase("jackInTheBox") is False

    assert is_camelcase("jackInTheBox")
    assert is_snakecase("jackInTheBox") is False
    assert is_pascalcase("jackInTheBox") is False

    assert is_camelcase("API")
    assert is_pascalcase("API")
    assert is_snakecase("API")


def test_numeric():
    assert camelize(1234) == 1234
    assert decamelize(123) == 123
    assert pascalize(123) == 123


def test_upper():
    assert camelize("API") == "API"
    assert decamelize("API") == "API"
    assert pascalize("API") == "API"
    assert depascalize("API") == "API"


def test_camelize():
    actual = camelize(
        {
            "videos": [
                {
                    "fallback_url": "https://media.io/video",
                    "scrubber_media_url": "https://media.io/video",
                    "dash_url": "https://media.io/video",
                },
            ],
            "images": [
                {
                    "fallback_url": "https://media.io/image",
                    "scrubber_media_url": "https://media.io/image",
                    "url": "https://media.io/image",
                },
            ],
            "other": [
                {
                    "_fallback_url": "https://media.io/image",
                    "__scrubber_media___url_": "https://media.io/image",
                    "_url__": "https://media.io/image",
                },
                {
                    "API": "test_upper",
                    "_API_": "test_upper",
                    "__API__": "test_upper",
                    "APIResponse": "test_acronym",
                    "_APIResponse_": "test_acronym",
                    "__APIResponse__": "test_acronym",
                },
            ],
        }
    )
    expected = {
        "videos": [
            {
                "fallbackUrl": "https://media.io/video",
                "scrubberMediaUrl": "https://media.io/video",
                "dashUrl": "https://media.io/video",
            },
        ],
        "images": [
            {
                "fallbackUrl": "https://media.io/image",
                "scrubberMediaUrl": "https://media.io/image",
                "url": "https://media.io/image",
            },
        ],
        "other": [
            {
                "_fallbackUrl": "https://media.io/image",
                "__scrubberMediaUrl_": "https://media.io/image",
                "_url__": "https://media.io/image",
            },
            {
                "API": "test_upper",
                "_API_": "test_upper",
                "__API__": "test_upper",
                "APIResponse": "test_acronym",
                "_APIResponse_": "test_acronym",
                "__APIResponse__": "test_acronym",
            },
        ],
    }
    assert actual == expected


def test_pascalize():
    actual = pascalize(
        {
            "videos": [
                {
                    "fallback_url": "https://media.io/video",
                    "scrubber_media_url": "https://media.io/video",
                    "dash_url": "https://media.io/video",
                },
            ],
            "images": [
                {
                    "fallback_url": "https://media.io/image",
                    "scrubber_media_url": "https://media.io/image",
                    "url": "https://media.io/image",
                },
            ],
            "other": [
                {
                    "_fallback_url": "https://media.io/image",
                    "__scrubber_media___url_": "https://media.io/image",
                    "_url__": "https://media.io/image",
                },
                {
                    "API": "test_upper",
                    "_API_": "test_upper",
                    "__API__": "test_upper",
                    "APIResponse": "test_acronym",
                    "_APIResponse_": "test_acronym",
                    "__APIResponse__": "test_acronym",
                },
            ],
        }
    )
    expected = {
        "Videos": [
            {
                "FallbackUrl": "https://media.io/video",
                "ScrubberMediaUrl": "https://media.io/video",
                "DashUrl": "https://media.io/video",
            },
        ],
        "Images": [
            {
                "FallbackUrl": "https://media.io/image",
                "ScrubberMediaUrl": "https://media.io/image",
                "Url": "https://media.io/image",
            },
        ],
        "Other": [
            {
                "_FallbackUrl": "https://media.io/image",
                "__ScrubberMediaUrl_": "https://media.io/image",
                "_Url__": "https://media.io/image",
            },
            {
                "API": "test_upper",
                "_API_": "test_upper",
                "__API__": "test_upper",
                "APIResponse": "test_acronym",
                "_APIResponse_": "test_acronym",
                "__APIResponse__": "test_acronym",
            },
        ],
    }
    assert actual == expected


def test_decamelize():
    actual = decamelize(
        [
            {
                "symbol": "AAL",
                "lastPrice": 31.78,
                "changePct": 2.8146,
                "impliedVolatality": 0.482,
            },
            {
                "symbol": "LBTYA",
                "lastPrice": 25.95,
                "changePct": 2.6503,
                "impliedVolatality": 0.7287,
            },
            {
                "_symbol": "LBTYK",
                "changePct_": 2.5827,
                "_lastPrice__": 25.42,
                "__impliedVolatality_": 0.4454,
            },
            {
                "API": "test_upper",
                "_API_": "test_upper",
                "__API__": "test_upper",
                "APIResponse": "test_acronym",
                "_APIResponse_": "test_acronym",
                "__APIResponse__": "test_acronym",
                "ruby_tuesdays": "ruby_tuesdays",
            },
        ]
    )
    expected = [
        {
            "symbol": "AAL",
            "last_price": 31.78,
            "change_pct": 2.8146,
            "implied_volatality": 0.482,
        },
        {
            "symbol": "LBTYA",
            "last_price": 25.95,
            "change_pct": 2.6503,
            "implied_volatality": 0.7287,
        },
        {
            "_symbol": "LBTYK",
            "change_pct_": 2.5827,
            "_last_price__": 25.42,
            "__implied_volatality_": 0.4454,
        },
        {
            "API": "test_upper",
            "_API_": "test_upper",
            "__API__": "test_upper",
            "api_response": "test_acronym",
            "_api_response_": "test_acronym",
            "__api_response__": "test_acronym",
            "ruby_tuesdays": "ruby_tuesdays",
        },
    ]

    assert actual == expected


def test_depascalize():
    actual = depascalize(
        [
            {
                "Symbol": "AAL",
                "LastPrice": 31.78,
                "ChangePct": 2.8146,
                "ImpliedVolatality": 0.482,
            },
            {
                "Symbol": "LBTYA",
                "LastPrice": 25.95,
                "ChangePct": 2.6503,
                "ImpliedVolatality": 0.7287,
            },
            {
                "_Symbol": "LBTYK",
                "ChangePct_": 2.5827,
                "_LastPrice__": 25.42,
                "__ImpliedVolatality_": 0.4454,
            },
            {
                "API": "test_upper",
                "_API_": "test_upper",
                "__API__": "test_upper",
                "APIResponse": "test_acronym",
                "_APIResponse_": "test_acronym",
                "__APIResponse__": "test_acronym",
                "ruby_tuesdays": "ruby_tuesdays",
            },
        ]
    )
    expected = [
        {
            "symbol": "AAL",
            "last_price": 31.78,
            "change_pct": 2.8146,
            "implied_volatality": 0.482,
        },
        {
            "symbol": "LBTYA",
            "last_price": 25.95,
            "change_pct": 2.6503,
            "implied_volatality": 0.7287,
        },
        {
            "_symbol": "LBTYK",
            "change_pct_": 2.5827,
            "_last_price__": 25.42,
            "__implied_volatality_": 0.4454,
        },
        {
            "API": "test_upper",
            "_API_": "test_upper",
            "__API__": "test_upper",
            "api_response": "test_acronym",
            "_api_response_": "test_acronym",
            "__api_response__": "test_acronym",
            "ruby_tuesdays": "ruby_tuesdays",
        },
    ]

    assert actual == expected


def test_replace_values():
    unhashable_value = set()
    actual = replace_values(
        {"k1": "origin1", "k2": {"k3": "origin2"}, "k4": unhashable_value},
        {"origin1": "translated", "origin2": "translated"},
    )
    assert actual == {
        "k1": "translated",
        "k2": {"k3": "translated"},
        "k4": unhashable_value,
    }
