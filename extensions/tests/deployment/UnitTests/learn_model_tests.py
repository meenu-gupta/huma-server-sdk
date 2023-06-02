import unittest

from extensions.common.s3object import S3Object
from extensions.deployment.models.learn import (
    LearnArticleContent,
    LearnArticleContentType,
)
from sdk.common.utils.convertible import ConvertibleClassValidationError


class LearnArticleContentTestCase(unittest.TestCase):
    @staticmethod
    def _sample_content():
        return {
            LearnArticleContent.TYPE: LearnArticleContentType.VIDEO.name,
            LearnArticleContent.TIME_TO_READ: "20m",
            LearnArticleContent.TEXT_DETAILS: "Here what you read",
        }

    def test_success_split_url_on_creation(self):
        url = "   https://some.com/  "
        learn_content_dict = {**self._sample_content(), LearnArticleContent.URL: url}
        learn_content = LearnArticleContent.from_dict(learn_content_dict)
        self.assertEqual(learn_content.url, url.strip())

    def test_success_create_article_content_with_content_object(self):
        learn_content_dict = {
            **self._sample_content(),
            LearnArticleContent.CONTENT_OBJECT: {
                S3Object.BUCKET: "integrationtests",
                S3Object.KEY: "shared/5ded7cfa844317000162d5e7/logo/Screenshot_1572653613.png",
                S3Object.REGION: "cn",
            },
        }
        try:
            learn_content = LearnArticleContent.from_dict(learn_content_dict)
        except ConvertibleClassValidationError:
            self.fail()
        else:
            self.assertIsNotNone(learn_content.contentObject)


if __name__ == "__main__":
    unittest.main()
