from pathlib import Path

import cv2
import numpy as np


def list_to_color(l: list) -> np.uint8:
    return np.uint8([[l]])


def read_file(path: Path) -> cv2.typing.MatLike:
    """ Reads an image file from path containing any symbols
        cv2.imread crashes if path contains cyrrilic letters 
    """
    with open(path, "rb") as file:
        chunk = file.read()
        chunk = np.frombuffer(chunk, dtype=np.uint8)
        return cv2.imdecode(chunk, cv2.IMREAD_COLOR)


def write_file(path: Path, image: cv2.typing.MatLike):
    # if not path.is_file():
    #     raise ValueError("path has to be a file.")
    
    _, image_buffer = cv2.imencode('.jpg', image)
    image_buffer.tofile(path)


def reverse_mask(mask: np.ndarray):
    if mask.ndim != 2:
        raise ValueError("mask dimension count must be 2.")
    
    mask = 255 - mask
    return mask

def imshow_mask(mask: np.ndarray):
    if mask.ndim != 2:
        raise ValueError("mask dimension count must be 2.")
    
    preview = np.zeros((*mask.shape, 3))
    preview[mask == 255] = [255] * 3

    cv2.imshow("Mask Preview", mask)
