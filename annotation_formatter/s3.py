import io
import re
import dataclasses
from typing import Union

import boto3


S3_URL_PATTERN = re.compile("^s3://(?P<bucket>[^/\s]+)(?:/(?P<prefix>[^\s]*?(?P<item>[^/\s]+)/?)?)?$")


@dataclasses.dataclass
class S3ConnectionConfig:
    region: str
    endpoint: str


@dataclasses.dataclass
class S3Credentials:
    access_key_id: str
    secret_access_key: str
    session_token: str


class S3Context:
    def __init__(self, connection: S3ConnectionConfig, credentials: S3Credentials):        
        self.session = boto3.session.Session(    
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token
        )
        self.resource = self.session.resource(
            service_name='s3',
            region_name=connection.region,
            endpoint_url=connection.endpoint
        )
    
    def download_bytes(self, object) -> bytes:
        if isinstance(object, str) and S3Url.is_s3_url(object):
            object = self.url_to_object(object)

        buffer = io.BytesIO()
        object.download_fileobj(buffer)
        return buffer.getvalue()
    
    def download_file(self, object, path):
        if isinstance(object, str) and S3Url.is_s3_url(object):
            object = self.url_to_object(object)

        object.download_file(path)

    def url_to_object(self, s3_url: Union[str, "S3Url"]):
        if isinstance(s3_url, str):
            s3_url = S3Url(s3_url)
        return self.resource.Bucket(s3_url.bucket).Object(s3_url.prefix)


class S3Url:
    def __init__(self, url: str):
        if (match := re.match(S3_URL_PATTERN, url)) is None:
            raise ValueError("Url is not s3")
        
        self.bucket = match.group("bucket")
        self.prefix = match.group("prefix") or ""
        self.item = match.group("item") or ""

    def __truediv__(self, to_append: str) -> "S3Url":
        # jank
        return S3Url(
            f"s3://{self.bucket}/{'' if not self.prefix else self.prefix + '/'}{to_append}"
    )

    @staticmethod
    def is_s3_url(url: str) -> bool:
        return re.match(S3_URL_PATTERN, url) is not None
    

__all__ = [
    "S3ConnectionConfig",
    "S3Credentials",
    "S3Context",
    "S3Url"
]
