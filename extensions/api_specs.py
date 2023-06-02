SPEC = {
    "endpoint": f'apispec_extensions',
    "route": f'/apispec_extensions.json',
    "rule_filter": lambda rule: True if rule.rule.startswith("/api/extensions") or
                                        rule.rule.startswith("/api/public") else False,
    "model_filter": lambda tag: True,  # all in
}

