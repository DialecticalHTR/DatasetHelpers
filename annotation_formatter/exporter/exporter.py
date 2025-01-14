import io
from pathlib import Path

from s3 import S3Url, S3Context

from .base import Exporter


class S3Exporter(Exporter):
    def __init__(self, s3: S3Context, base_url: str | S3Url):
        self.s3 = s3

        if isinstance(base_url, str):
            base_url = S3Url(base_url)
        self.base_url = base_url

    def export_bytes(self, bytes, path: str):
        target_url = self._get_target_path(path)
        object = self.s3.url_to_object(target_url)

        with io.BytesIO(bytes) as input_file:
            object.upload_fileobj(input_file)

    def export_file(self, file, path):
        target_url = self._get_target_path(path)
        object = self.s3.url_to_object(target_url)
        object.upload_fileobj(file)
    
    def _get_target_path(self,path) -> S3Url:
        return self.base_url / path


class FolderExporter(Exporter):
    def __init__(self, base_path: Path):
        self.base_path = base_path.resolve()
    
    def export_bytes(self, bytes, path: str):
        path = self.base_path / path
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as output_file:
            output_file.write(bytes)

    def export_file(self, input_file, path):
        path = self.base_path / path
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as output_file:
            output_file.write(input_file.read())
    
    def _get_target_path(self, path) -> Path:
        return self.base_path / path


__all__ = [
    "S3Exporter",
    "FolderExporter"
]
