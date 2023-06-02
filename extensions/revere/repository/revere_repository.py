import json
import os
from abc import ABC, abstractmethod

from extensions.revere.models.revere import RevereTest, RevereTestResult

here = os.path.dirname(os.path.realpath(__file__))


class RevereTestRepository(ABC):
    @abstractmethod
    def create_test(self, user_id: str, deployment_id: str, module_name: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def retrieve_test(self, user_id: str, test_id: str) -> RevereTest:
        raise NotImplementedError

    @abstractmethod
    def retrieve_user_tests(self, user_id: str, status: str) -> list[RevereTest]:
        raise NotImplementedError

    @abstractmethod
    def finish_test(self, user_id: str, test_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_word_list_result(
        self, test_id: str, user_id: str, result: RevereTestResult
    ) -> None:
        raise NotImplementedError

    @staticmethod
    def retrieve_homophones():
        homophones_path = os.path.join(here, "../data/homophones.json")
        with open(homophones_path, "r") as jsfile:
            data = jsfile.read()
            homophones_dict = json.loads(data)
        return homophones_dict

    @staticmethod
    def retrieve_initial_word_lists():
        path = os.path.join(here, "../data/initial_word_lists.json")
        with open(path, "r") as jsfile:
            data = jsfile.read()
            words_dict = json.loads(data)
        return words_dict["a"], words_dict["b"]
