import uuid
from copy import copy

from extensions.deployment.models.deployment import Deployment
from extensions.tests.deployment.IntegrationTests.abstract_deployment_test_case_tests import (
    AbstractDeploymentTestCase,
)
from sdk.common.exceptions.exceptions import ErrorCodes


def simple_article():
    return {
        "title": "article_ss three",
        "order": 10,
        "type": "SMALL",
        "thumbnailUrl": {
            "region": "us-west-1",
            "key": "my.png",
            "bucket": "admin_bucket",
        },
        "content": {
            "type": "VIDEO",
            "timeToRead": "20m",
            "textDetails": "Here what you read",
            "videoUrl": {
                "bucket": "integrationtests",
                "key": "shared/5ded7cfa844317000162d5e7/logo/Screenshot_1572653613.png",
                "region": "cn",
            },
        },
    }


class LearnSectionTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        self.learn_url = (
            f"{self.deployment_route}/deployment/{self.deployment_id}/learn-section"
        )
        self.createLearnBody = {"title": "Test section", "order": 10}
        self.updateLearnBody = {"title": "Updated section", "order": 9}

    def test_learn_creation(self):
        deployment = self.get_deployment()
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]
        body = self.createLearnBody
        rsp = self.flask_client.post(
            f"{self.learn_url}", json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)
        deployment = self.get_deployment()
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

    def test_learn_creation_with_id(self):
        body = copy(self.createLearnBody)
        body["id"] = str(uuid.uuid4())
        rsp = self.flask_client.post(
            f"{self.learn_url}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_learn_creation_with_date(self):
        body = copy(self.createLearnBody)
        body["createDateTime"] = "2020-04-07T17:05:51"
        rsp = self.flask_client.post(
            f"{self.learn_url}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_learn_creation_for_not_existing_deployment(self):
        body = copy(self.createLearnBody)
        deployment_id = "5d386cc6ff885918d96edb5c"
        learn_url = f"{self.deployment_route}/deployment/{deployment_id}/learn-section"
        rsp = self.flask_client.post(f"{learn_url}", json=body, headers=self.headers)
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def test_learn_section_update(self):
        deployment = self.get_deployment()
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        body = self.updateLearnBody
        rsp = self.flask_client.put(
            f"{self.learn_url}/{self.section_id}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)
        self.assertEqual(self.section_id, rsp.json["id"])

        deployment = self.get_deployment()
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

    def test_learn_section_delete(self):
        deployment = self.get_deployment()
        old_key_actions_count = len(deployment[Deployment.KEY_ACTIONS])
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        rsp = self.flask_client.delete(
            f"{self.learn_url}/{self.section_id}", headers=self.headers
        )
        self.assertEqual(204, rsp.status_code)

        deployment = self.get_deployment()
        new_key_action_count = len(deployment[Deployment.KEY_ACTIONS])
        self.assertLess(new_key_action_count, old_key_actions_count)
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])


class LearnArticleTestCase(AbstractDeploymentTestCase):
    def setUp(self):
        super().setUp()
        delete_article_url_template = f"%s/deployment/%s/learn-section/%s/article"
        self.article_url = delete_article_url_template % (
            self.deployment_route,
            self.deployment_id,
            self.section_id,
        )
        self.article_id = "5e8c58176207e5f78023e655"
        self.fake_id = "5d386cc6ff885918d96edc2c"

    def test_learn_article_create(self):
        deployment = self.get_deployment()
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        body = simple_article()
        rsp = self.flask_client.post(
            f"{self.article_url}", json=body, headers=self.headers
        )
        self.assertEqual(201, rsp.status_code)

        deployment = self.get_deployment()
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

    def test_learn_article_create_with_id(self):
        article = simple_article()
        article["id"] = self.article_id
        body = article
        rsp = self.flask_client.post(
            f"{self.article_url}", json=body, headers=self.headers
        )
        self.assertEqual(403, rsp.status_code)
        self.assertEqual(ErrorCodes.DATA_VALIDATION_ERROR, rsp.json["code"])

    def test_learn_article_create_deployment_does_not_exist(self):
        body = simple_article()
        article_url = f"{self.deployment_route}/deployment/{self.fake_id}/learn-section/{self.section_id}/article"
        rsp = self.flask_client.post(f"{article_url}", json=body, headers=self.headers)
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(300012, rsp.json["code"])

    def test_learn_article_update(self):
        deployment = self.get_deployment()
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        body = simple_article()
        rsp = self.flask_client.put(
            f"{self.article_url}/{self.article_id}", json=body, headers=self.headers
        )
        self.assertEqual(200, rsp.status_code)

        deployment = self.get_deployment()
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])

    def test_learn_article_update_deployment_does_not_exist(self):
        body = simple_article()
        article_url = f"{self.article_url}/{self.fake_id}"
        rsp = self.flask_client.put(f"{article_url}", json=body, headers=self.headers)
        self.assertEqual(404, rsp.status_code)
        self.assertEqual(100003, rsp.json["code"])

    def test_learn_article_delete(self):
        deployment = self.get_deployment()
        old_key_actions_count = len(deployment["keyActions"])
        old_update_date = deployment[Deployment.UPDATE_DATE_TIME]

        rsp = self.flask_client.delete(
            f"{self.article_url}/{self.article_id}", headers=self.headers
        )
        self.assertEqual(204, rsp.status_code)

        deployment = self.get_deployment()
        new_key_action_count = len(deployment["keyActions"])

        self.assertLess(new_key_action_count, old_key_actions_count)
        self.assertLess(old_update_date, deployment[Deployment.UPDATE_DATE_TIME])
