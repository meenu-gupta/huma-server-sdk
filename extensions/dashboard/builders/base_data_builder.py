import abc
from abc import ABC


class DataBuilder(ABC):
    from extensions.dashboard.models.gadgets.base_gadget import GadgetConfig, Gadget

    config: GadgetConfig = None
    gadget: Gadget = None

    def execute(self, gadget: Gadget):
        self.config = gadget.configuration
        self.gadget = gadget
        if self.is_valid():
            return self.run()

    def run(self):
        return self.build_data()

    def is_valid(self):
        return bool(self.config.configured)

    @abc.abstractmethod
    def build_data(self):
        raise NotImplementedError
