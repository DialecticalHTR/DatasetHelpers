from abc import ABC, abstractmethod


class Exporter(ABC):
    @abstractmethod
    def export_bytes(self, bytes, path: str):
        pass

    @abstractmethod
    def export_file(self, file, path: str):
        pass


__all__ = [
    'Exporter'
]
