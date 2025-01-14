import dataclasses


@dataclasses.dataclass
class Region:
    id: str
    text: str = dataclasses.field(init=False)
    type: str = dataclasses.field(init=False)
    image_rotation: int = dataclasses.field(init=False)
    labels: list[str] = dataclasses.field(default_factory=list)
    points: list[list[int, int]] = dataclasses.field(default_factory=list)
    
    def process_part(self, part):
        annotation_type = part['type']
        value = part['value']
        self.image_rotation = part['image_rotation']

        match annotation_type:
            case 'labels':
                self.labels = value['labels']
            case 'textarea':
                # TODO: make text an list with all text annotations, will do for now
                self.text = value['text'][0]
            case 'rectangle':
                self.type = annotation_type
                x, y, w, h = value['x'], value['y'], value['width'], value['height']

                self.points.append([x, y])
                self.points.append([x+w, y])
                self.points.append([x+w, y+h])
                self.points.append([x, y+h])
                self.points.append(self.points[0])
            case 'polygon':
                self.type = annotation_type
                for x, y in value['points']:
                    self.points.append([round(x), round(y)])
                self.points.append(self.points[0])
            case _:
                pass


@dataclasses.dataclass
class Annotation:
    id: str
    regions: dict[str, Region] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_json(cls, data) -> "Annotation":
        annotation = cls(id=data['id'])

        for region_part in data['result']:
            if (region_id := region_part['id']) not in annotation.regions:
                annotation.regions[region_id] = Region(id=region_id)
            annotation.regions[region_id].process_part(region_part)
        return annotation


@dataclasses.dataclass
class Task:
    id: str
    image_url: str = dataclasses.field(init=False)
    annotations: list[Annotation] = dataclasses.field(default_factory=list)


__all__ = [
    'Task',
    'Annotation',
    'Region'
]
