from abc import ABC, abstractmethod
from typing import List

from s3 import S3Context
from exporter import Exporter


class Builder(ABC):
    def __init__(self, s3_context: S3Context):
        self.s3_context = s3_context

    @abstractmethod
    def build_dataset(exporters: List[Exporter]):
        pass


__all__ = [
    'Builder'
]
