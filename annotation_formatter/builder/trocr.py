import io
import csv
from typing import List

import cv2
import numpy as np

from annotations import Task
from exporter import Exporter
from .base import Builder


class TrOCRBuilder(Builder):
    def build_dataset(self, tasks: List[Task], exporters: List[Exporter]):
        data = []

        for task_data in tasks:
            image_bytes = self.s3_context.download_bytes(task_data.image_url)
            image_bytes = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

            for annotation in task_data.annotations:
                for region_id, region in annotation.regions.items():
                    print('Processing', region_id)

                    # create contour out of label studio points
                    image_height, image_width = image.shape[:2]
                    contour = [[x / 100 * image_width, y / 100 * image_height] for x, y in region.points]
                    contour = np.array(contour).reshape((-1,1,2)).astype(np.int32)

                    # get contour bounding box
                    x, y, w, h = cv2.boundingRect(contour)

                    # create mask
                    mask = np.zeros([image_height, image_width], dtype=np.uint8)
                    cv2.fillPoly(mask, [contour], 255)
                    
                    # crop mask and image
                    mask = mask[y:y+h, x:x+w]
                    image_part = image[y:y+h, x:x+w]

                    # mask shenanigans
                    text_part = cv2.bitwise_and(image_part, image_part, mask=mask)
                    white_bg = np.full_like(image_part, 255)
                    white_part = cv2.bitwise_and(white_bg, white_bg, mask=cv2.bitwise_not(mask))

                    image_part = cv2.add(text_part, white_part)

                    # rotate image if it was rotated in Label Studio
                    rotation_matrix = cv2.getRotationMatrix2D(
                        np.array(image_part.shape[1::-1]) / 2,
                        region.image_rotation,
                        1.0
                    )
                    image_part = cv2.warpAffine(image_part, rotation_matrix, image_part.shape[1::-1], flags=cv2.INTER_CUBIC)

                    # save image
                    filename = f'{region_id}.jpg'
                    _, image_buffer = cv2.imencode('.jpg', image_part)
                    image_bytes = image_buffer.tobytes()

                    for exporter in exporters:
                        exporter.export_bytes(image_bytes, f"images/{region.id}.jpg")

                    # add to data csv
                    data.append({
                        'image': filename,
                        'text': region.text
                    })
        
        with io.StringIO() as csv_file:
            csv_writer = csv.DictWriter(csv_file, 
                                        fieldnames=['image', 'text'], 
                                        delimiter=';', 
                                        dialect='unix',
                                        escapechar='\\',
                                        quoting=csv.QUOTE_NONE)
            csv_writer.writeheader()
            csv_writer.writerows(data)
            csv_file.seek(0)
            csv_data = csv_file.read()
        
        csv_bytes = csv_data.encode(encoding='utf-8')
        for exporter in exporters:
            exporter.export_bytes(csv_bytes, 'data.csv')


__all__ = [
    'TrOCRBuilder'
]
