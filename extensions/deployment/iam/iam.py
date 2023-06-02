from collections import defaultdict
from functools import wraps

from flask import Blueprint, g

from extensions.authorization.models.role.default_permissions import PolicyType
from extensions.authorization.models.role.role import Role
from extensions.common.policies import is_self_request
from sdk.common.exceptions.exceptions import PermissionDenied


class IAMBlueprint(Blueprint):
    def __init__(self, *args, **kwargs):
        self.router_functions = defaultdict(list)
        self.policy = kwargs.pop("policy", None)
        self.policy_enabled = kwargs.pop("policy_enabled", True)
        super(IAMBlueprint, self).__init__(*args, **kwargs)

    def add_policy(self, endpoint, policy, override=False):
        if override or endpoint not in self.router_functions:
            self.router_functions[endpoint].append((policy, override))
        else:
            overridable = not any(ovr for _, ovr in self.router_functions[endpoint])
            if overridable:
                self.router_functions[endpoint].append((policy, override))

    def get_endpoint_policies(self, endpoint: str) -> list:
        policies = sum(map(lambda p: p[0], self.router_functions[endpoint]), [])
        endpoint_policies = [p() if callable(p) else p for p in policies]
        flattened_endpoint_policies = []
        for policy_item in endpoint_policies:
            if isinstance(policy_item, list):
                flattened_endpoint_policies.extend(policy_item)
            else:
                flattened_endpoint_policies.append(policy_item)
        return list(filter(None, flattened_endpoint_policies))

    @staticmethod
    def check_required(endpoint_policies: list[PolicyType]):
        is_own_profile_policy = endpoint_policies == [PolicyType.VIEW_OWN_PROFILE]
        if is_self_request() and is_own_profile_policy:
            return False
        return True

    def require_policy(self, policy, override=False):
        policies = policy if isinstance(policy, list) else [policy]

        def decorator(func):
            endpoint = func.__name__

            @wraps(func)
            def inner(*args, **kwargs):
                if self.policy_enabled:
                    endpoint_policies = self.get_endpoint_policies(endpoint)
                    self.check_permissions(endpoint_policies)
                return func(*args, **kwargs)

            is_first_call = endpoint not in self.router_functions
            self.add_policy(endpoint, policies, override)
            if is_first_call:
                return inner
            return func

        return decorator

    @staticmethod
    def check_permissions(endpoint_policies: list[PolicyType]):
        if not endpoint_policies:
            return

        role = g.authz_user.get_role()
        if (
            not IAMBlueprint.check_required(endpoint_policies)
            and role.userType != Role.UserType.SERVICE_ACCOUNT
        ):
            return

        if not role or not role.has(endpoint_policies):
            raise PermissionDenied

    def route(self, rule, **options):
        def decorator(f):
            f = self.require_policy(self.policy, False)(f)
            super(IAMBlueprint, self).route(rule, **options)(f)
            return f

        return decorator

    def get(self, rule, **options):
        def decorator(f):
            f = self.require_policy(self.policy, False)(f)
            super(IAMBlueprint, self).get(rule, **options)(f)
            return f

        return decorator

    def post(self, rule, **options):
        def decorator(f):
            f = self.require_policy(self.policy, False)(f)
            super(IAMBlueprint, self).post(rule, **options)(f)
            return f

        return decorator

    def put(self, rule, **options):
        def decorator(f):
            f = self.require_policy(self.policy, False)(f)
            super(IAMBlueprint, self).put(rule, **options)(f)
            return f

        return decorator
