import io
from io import BytesIO
from typing import Union

from sdk.common.usecase.response_object import Response
from sdk.common.utils.convertible import convertibleclass, default_field


class DownloadFileResponseObject(Response):
    @convertibleclass
    class Response:
        content: BytesIO = default_field()
        contentLength: int = default_field()
        contentType: str = default_field()

    def __init__(
        self, content: Union[io.BytesIO, bytes], content_length: int, content_type: str
    ):
        if isinstance(content, bytes):
            content = io.BytesIO(content)
        super().__init__(
            value=self.Response(
                content=content, contentType=content_type, contentLength=content_length
            )
        )


class GetSignedUrlResponseObject(Response):
    @convertibleclass
    class Response:
        url: str = default_field()

    def __init__(self, url: str):
        super().__init__(value=self.Response(url=url))


class UploadFileResponseObjectV1(Response):
    @convertibleclass
    class Response:
        ID = "id"
        id: str = default_field()

    def __init__(self, id: str):
        super().__init__(value=self.Response(id=id))


class DownloadFileResponseObjectV1(Response):
    @convertibleclass
    class Response:
        fileName: str = default_field()
        content: BytesIO = default_field()
        contentLength: int = default_field()
        contentType: str = default_field()

    def __init__(
        self,
        fileName: str,
        content: Union[io.BytesIO, bytes],
        content_length: int,
        content_type: str,
    ):
        if isinstance(content, bytes):
            content = io.BytesIO(content)
        super().__init__(
            value=self.Response(
                fileName=fileName,
                content=content,
                contentType=content_type,
                contentLength=content_length,
            )
        )


class GetSignedUrlResponseObjectV1(Response):
    @convertibleclass
    class Response:
        URL = "url"
        FILE_NAME = "fileName"
        FILE_SIZE = "fileSize"
        CONTENT_TYPE = "contentType"

        url: str = default_field()
        fileName: str = default_field()
        fileSize: int = default_field()
        contentType: str = default_field()

    def __init__(self, url: str, file_name: str, file_size: int, content_type: str):
        super().__init__(
            value=self.Response(
                url=url,
                fileName=file_name,
                fileSize=file_size,
                contentType=content_type,
            )
        )
