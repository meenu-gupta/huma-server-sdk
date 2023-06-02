from sdk.common.adapter.token_adapter import TokenAdapter
from sdk.common.utils import inject
from sdk.common.utils.token.jwt.jwt import decode_jwt_from_headers


def verify_jwt_in_request():
    token_adapter = inject.instance(TokenAdapter)
    encoded_token = decode_jwt_from_headers()
    return token_adapter.verify_token(encoded_token)
