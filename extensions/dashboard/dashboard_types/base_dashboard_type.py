from abc import ABC, abstractmethod


class DashboardType(ABC):
    dashboard_id = ""

    @abstractmethod
    def generate_template(self, resource_name: str) -> dict:
        raise NotImplementedError

    @property
    @abstractmethod
    def gadgets(self):
        return NotImplementedError
