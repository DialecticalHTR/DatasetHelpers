import json
from typing import Dict
from pathlib import Path

from .models import *
from s3 import S3Url, S3Context

from .base import AnnotationLoader


class S3AnnotationLoader(AnnotationLoader):
    def __init__(self, s3: S3Context):
        self.s3 = s3

    def get_tasks(self, s3_url: str | S3Url):
        if isinstance(s3_url, str):
            s3_url = S3Url(s3_url)

        tasks: Dict[str, Task] = {}
        bucket =  self.s3.resource.Bucket(s3_url.bucket)
        for object_summary in bucket.objects.filter(Prefix=s3_url.prefix):
            object = bucket.Object(object_summary.key)
            data = self.s3.download_bytes(object)
            data = json.loads(data)

            task_data = data['task']
            if (task_id := task_data['id']) not in tasks:
                tasks[task_id] = Task(id=task_data['id'])
                tasks[task_id].image_url = task_data['data']['ocr']
            tasks[task_id].annotations.append(Annotation.from_json(data))
        return tasks.values()


class ExportAnnotationLoader(AnnotationLoader):
    def __init__(self):
        pass

    def get_tasks(self, filepath: str | Path):
        if isinstance(filepath, str):
            filepath = Path(filepath)
        if not filepath.exists():
            raise ValueError("Path doesn't exist")
        if not filepath.is_file():
            raise ValueError("Path is not a file")
        
        tasks = []
        with open(filepath, mode='r', encoding='utf-8') as file:
            data = json.load(file)

            for task_data in data:
                task = Task(task_data["id"])
                task.image_url = task_data['data']['ocr']
                for annotation in task_data['annotations']:
                    task.annotations.append(Annotation.from_json(annotation))
                tasks.append(task)
        return tasks


__all__ = [
    "S3AnnotationLoader",
    "ExportAnnotationLoader"
]
