import abc
from abc import ABC
from typing import Union

from extensions.module_result.models.primitives import Primitive


class IntegrationClient(ABC):
    @abc.abstractmethod
    def call_api_endpoint(self, primitive: Primitive) -> Union[Primitive, None]:
        """ Send a primitive to the integration. All Primitives must be for a single user. """
        raise NotImplementedError
