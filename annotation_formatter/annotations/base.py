from abc import abstractmethod, ABC
from typing import Any, List

from .models import Task


class AnnotationLoader(ABC):
    @abstractmethod
    def get_tasks(self, path: Any) -> List[Task]:
        pass


__all__ = [
    'AnnotationLoader'
]
