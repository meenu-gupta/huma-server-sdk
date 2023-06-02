from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from pymongo.client_session import ClientSession

from extensions.common.sort import SortField
from extensions.module_result.models.primitives import Primitive
from extensions.module_result.module_result_utils import AggregateFunc, AggregateMode


class ModuleResultRepository(ABC):
    @abstractmethod
    def create_primitive(self, primitive: Primitive, save_unseen: bool = False) -> str:
        raise NotImplementedError

    @abstractmethod
    def flush_unseen_results(
        self, user_id: str, start_date_time: datetime, module_id: str = None
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def reset_flags(
        self,
        user_id: str,
        module_id: str,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def retrieve_unseen_results(
        self,
        deployment_id: str,
        user_id: str,
        module_ids: list[str],
        enabled_module_ids: list[str] = None,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_first_unseen_result(
        self, deployment_id: str, user_id: str
    ) -> Optional[datetime]:
        raise NotImplementedError

    @abstractmethod
    def calculate_unseen_flags(
        self,
        user_id: str,
        module_config_ids: list[str],
        excluded_modules_ids: list[str],
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def retrieve_primitives(
        self,
        user_id: str,
        module_id: str,
        primitive_name: str,
        skip: int,
        limit: int,
        direction: SortField.Direction,
        from_date_time: datetime = None,
        to_date_time: datetime = None,
        field_filter: dict = None,
        excluded_fields: list[str] = None,
        module_config_id: str = None,
        exclude_module_ids: list[str] = None,
    ) -> list[Primitive]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_aggregated_results(
        self,
        module_type: str,
        aggregation_function: AggregateFunc,
        mode: AggregateMode,
        start_date: datetime,
        end_date: datetime,
        skip: int = None,
        limit: int = None,
        user_id: str = None,
        module_config_id: str = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def retrieve_primitive(
        self, user_id: str, primitive_name: str, primitive_id: str
    ) -> Primitive:
        raise NotImplementedError

    @abstractmethod
    def retrieve_primitive_by_name(
        self,
        user_id: str,
        primitive_name: str,
        **filter_options,
    ) -> Primitive:
        raise NotImplementedError

    @abstractmethod
    def delete_user_primitive(
        self, user_id: str, primitive_names: list[str], session: ClientSession = None
    ):
        raise NotImplementedError

    @abstractmethod
    def create_indexes(self):
        raise NotImplementedError
