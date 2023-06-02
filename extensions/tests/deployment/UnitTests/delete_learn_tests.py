from unittest import TestCase
from unittest.mock import patch, MagicMock

from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.key_action_config import KeyActionConfig
from extensions.deployment.models.learn import LearnSection, Learn, LearnArticle
from extensions.deployment.router.deployment_requests import (
    DeleteLearnSectionRequestObject,
    DeleteArticleRequestObject,
)
from extensions.deployment.use_case.delete_learn_article_use_case import (
    DeleteLearnArticleUseCase,
)
from extensions.deployment.use_case.delete_learn_section_use_case import (
    DeleteLearnSectionUseCase,
)
from extensions.module_result.models.module_config import ModuleConfig


def get_deployment():
    return Deployment(
        id="test",
        name="test",
        learn=Learn(
            sections=[
                LearnSection(
                    id="section_test",
                    title="section_test",
                    articles=[
                        LearnArticle(id="article_test1", title="article_test1"),
                        LearnArticle(id="article_test2", title="article_test2"),
                    ],
                )
            ]
        ),
        moduleConfigs=[
            ModuleConfig(id="module_test1", learnArticleIds=["article_test1"]),
            ModuleConfig(id="module_test2", learnArticleIds=["article_test1"]),
            ModuleConfig(id="module_test3", learnArticleIds=["article_test2"]),
        ],
        keyActions=[
            KeyActionConfig(id="key_action_test1", learnArticleId="article_test1"),
            KeyActionConfig(id="key_action_test1", learnArticleId="article_test2"),
        ],
    )


class MockRepo:
    delete_learn_section = MagicMock()
    delete_learn_article = MagicMock()
    retrieve_deployment = MagicMock()
    retrieve_deployment.return_value = get_deployment()


class MockService(MagicMock):
    delete_key_action = MagicMock()
    create_or_update_module_config = MagicMock()


class DeleteLearnTests(TestCase):
    def setUp(self) -> None:
        MockRepo.retrieve_deployment.reset_mock()
        MockRepo.retrieve_deployment.return_value = get_deployment()
        MockService.delete_key_action.reset_mock()
        MockService.create_or_update_module_config.reset_mock()

    @patch(
        "extensions.deployment.use_case.delete_learn_use_case.DeploymentService",
        MockService,
    )
    def test_delete_section(self):
        use_case = DeleteLearnSectionUseCase(MockRepo())
        request_object = DeleteLearnSectionRequestObject(
            deploymentId="test", sectionId="section_test"
        )
        use_case.execute(request_object)
        MockRepo.retrieve_deployment.assert_called_once()
        self.assertEqual(3, MockService.create_or_update_module_config.call_count)
        self.assertEqual(2, MockService.delete_key_action.call_count)

    @patch(
        "extensions.deployment.use_case.delete_learn_use_case.DeploymentService",
        MockService,
    )
    def test_delete_article(self):
        use_case = DeleteLearnArticleUseCase(MockRepo())
        use_case.service = MockService()
        request_object = DeleteArticleRequestObject(
            deploymentId="test", sectionId="section_test", articleId="article_test1"
        )
        use_case.execute(request_object)
        MockRepo.retrieve_deployment.assert_called_once()
        self.assertEqual(2, MockService.create_or_update_module_config.call_count)
        MockService.create_or_update_module_config.reset_mock()
        MockService.delete_key_action.assert_called_once()
        MockService.delete_key_action.reset_mock()
