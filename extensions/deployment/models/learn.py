from datetime import datetime
from enum import Enum

from extensions.common.s3object import S3Object
from extensions.deployment.models.localizable import Localizable
from sdk.common.utils.convertible import (
    convertibleclass,
    meta,
    required_field,
    url_field,
    default_field,
)
from sdk.common.utils.validators import (
    validate_object_id,
    default_datetime_meta,
    validate_len,
)


@convertibleclass
class LearnArticleType(Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    BIG = "BIG"
    VIDEO = "VIDEO"


@convertibleclass
class LearnArticleContentType(Enum):
    TITLE_VIDEO_CONTENT = "TITLE_VIDEO_CONTENT"
    VIDEO = "VIDEO"
    LINK = "LINK"


@convertibleclass
class LearnArticleContent:
    ID = "id"
    TYPE = "type"
    TIME_TO_READ = "timeToRead"
    TEXT_DETAILS = "textDetails"
    VIDEO_URL = "videoUrl"
    URL = "url"
    CONTENT_OBJECT = "contentObject"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    type: LearnArticleContentType = required_field()
    timeToRead: str = default_field(metadata=meta(validate_len(1, 25)))
    textDetails: str = default_field(metadata=meta(validate_len(1, 100000)))
    videoUrl: S3Object = default_field()
    url: str = url_field(metadata=meta(validate_len(1, 1000)))
    contentObject: S3Object = default_field()


@convertibleclass
class LearnArticle(Localizable):
    ID = "id"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    TITLE = "title"
    TYPE = "type"
    CONTENT = "content"
    THUMBNAIL_URL = "thumbnailUrl"
    ORDER = "order"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    title: str = required_field(metadata=meta(validate_len(1, 100)))
    type: LearnArticleType = required_field()
    thumbnailUrl: S3Object = default_field()
    order: int = default_field()
    content: LearnArticleContent = required_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    _localizableFields: tuple[str, ...] = (TITLE,)

    def is_valid_for(self, role: str):
        return True


@convertibleclass
class OrderUpdateObject:
    ID = "id"
    ORDER = "order"

    id: str = required_field(metadata=meta(validate_object_id))
    order: int = required_field()


@convertibleclass
class LearnSection(Localizable):
    ID = "id"
    ARTICLES = "articles"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"
    ORDER = "order"
    TITLE = "title"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    title: str = default_field(metadata=meta(validate_len(1, 100)))
    order: int = default_field()
    articles: list[LearnArticle] = default_field()
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())

    _localizableFields: tuple[str, ...] = (TITLE, ARTICLES)

    def prepare_for_role(self, role: str):
        articles = self.articles or []
        articles = [article for article in articles if article.is_valid_for(role)]
        self.articles = articles


@convertibleclass
class Learn(Localizable):
    ID = "id"
    SECTIONS = "sections"
    SECTION_ID = f"{SECTIONS}.{LearnSection.ID}"
    ARTICLE_ID = f"{SECTIONS}.{LearnSection.ARTICLES}.{LearnArticle.ID}"
    CREATE_DATE_TIME = "createDateTime"
    UPDATE_DATE_TIME = "updateDateTime"

    id: str = default_field(metadata=meta(validate_object_id, value_to_field=str))
    updateDateTime: datetime = default_field(metadata=default_datetime_meta())
    createDateTime: datetime = default_field(metadata=default_datetime_meta())
    sections: list[LearnSection] = default_field()

    _localizableFields: tuple[str, ...] = (SECTIONS,)
