import os
from pathlib import Path
from typing import Tuple

import numpy as np
import cv2

from utils import *


current_path = Path(".").absolute()
input_path = current_path / "input"
output_path = current_path / "output"

DEBUGGING = 0
TEST_FILE = input_path / "Б" / "б004.jpg"


def get_hsv_bounds(color) -> Tuple[np.uint8, np.uint8]:
    if isinstance(color, list):
        color = list_to_color(color)
    color = cv2.cvtColor(color, cv2.COLOR_RGB2HSV)

    lower_bound = np.uint8((max(0,   np.int64(color[0][0][0]) - 10), 100, 100))
    upper_bound = np.uint8((min(255, np.int64(color[0][0][0]) + 10), 255, 255))

    return lower_bound, upper_bound


def get_card_mask(img, bg_color) -> np.ndarray:
# 1. Convert image BGR to HSV
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 2. Get lower and upper bound of background color
    lower_bound, upper_bound = get_hsv_bounds(bg_color)

    # 3. Get background mask
    mask = cv2.inRange(hsv_img, lower_bound, upper_bound)

    if DEBUGGING:
        imshow_mask(mask)
        cv2.waitKey(0)

    # 4. Add components outside of blue paper to removal mask
    x, y, w, h = cv2.boundingRect(mask)
    numLabels, labels, stats, _ = cv2.connectedComponentsWithStats(reverse_mask(mask))

    # Find max area component (should be blue paper), will be ignored while removing borders
    max_area_component = sorted(range(numLabels), key=lambda label: stats[label, cv2.CC_STAT_AREA], reverse=True)[0]
    for component in range(numLabels):
        if component == max_area_component:
            continue

        stat = stats[component]
        left, top = stat[cv2.CC_STAT_LEFT], stat[cv2.CC_STAT_TOP]
        right, bottom = left + stat[cv2.CC_STAT_WIDTH], top + stat[cv2.CC_STAT_HEIGHT]

        if left == 0 or top == 0 or right == w or bottom == h:
            mask[labels == component] = 255

    if DEBUGGING:
        imshow_mask(mask)
        cv2.waitKey(0)    

    # 5. Dilate and erode to remove artifacts on the card 
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=2)
    if DEBUGGING:
        imshow_mask(mask)
        cv2.waitKey(0)
    return mask


def normalize_card_rotation(img) -> cv2.typing.MatLike:
    """ TODO: rotate card in a way that would be close to an unrotated rectangle """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

    # Использование самого большого контура (предполагается, что это карточка)
    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)
        # preview = cv2.drawContours(img, largest_contour, -1, [0, 0, 255], 3)
        # cv2_imshow(preview)

        # Вычисление минимального ограничивающего прямоугольника
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        
        # Получение угла поворота
        angle = rect[2]
        if (angle >= 45):
            angle -= 90

        # Поворот изображения на вычисленный угол
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_img = cv2.warpAffine(
            img, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC
        )

        return rotated_img

    return img  # Возвращаем исходное изображение, если контуры не найдены


# https://stackoverflow.com/questions/50899692/most-dominant-color-in-rgb-image-opencv-numpy-python
def bincount_app(a):
    a2D = a.reshape(-1,a.shape[-1])
    col_range = (256, 256, 256) # generically : a2D.max(0)+1
    a1D = np.ravel_multi_index(a2D.T, col_range)
    return np.unravel_index(np.bincount(a1D).argmax(), col_range)


def fill_card_void(img) -> cv2.typing.MatLike:
    """ Replaces black parts of card image with average img color """
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = np.all(hsv_img < 10, axis=2)
    img[mask] = bincount_app(img)

    return img


def process_scan(img: cv2.typing.MatLike) -> list[cv2.typing.MatLike]:
    # 0. Scale it for better demonstration
    if DEBUGGING:
        img = cv2.resize(img, (0, 0), fx=0.2, fy=0.2)
    height, width = img.shape[0], img.shape[1]

    # 1. Remove blue background
    bg_color = [90, 195, 243]
    card_mask = get_card_mask(img, bg_color)
    img[card_mask == 255] = [0, 0, 0]

    # 2. Prepare for canny edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(card_mask, (5, 5), 0)
    
    # 3. Detect edges
    edges = cv2.Canny(blur, 100, 150)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)
    contours = [c for c, h in zip(contours, hierarchy[0]) if h[3] < 0]
    
    if DEBUGGING:
        preview = img.copy()
        preview = cv2.drawContours(preview, contours, -1, [0, 0, 255], 3)
        cv2.imshow("countours preview", preview)

    card_countours = []
    for contour in contours:
        # Approximate contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Expecting each card to be a rectangle
        if len(approx):
            (x, y, w, h) = cv2.boundingRect(approx)

            # Remove small artifacts
            if w > width * 0.2 and h > height * 0.2:
                card_countours.append(approx)
    
    card_images = []
    for i, countour in enumerate(card_countours):
        x, y, w, h = cv2.boundingRect(countour)
        card = img[y:y + h, x:x + w]
        
        # Normalize rotation
        if h > w:
            card = cv2.rotate(card, cv2.ROTATE_90_CLOCKWISE)
        card = normalize_card_rotation(card)

        # Remove edge artifacts
        mask = cv2.inRange(card, (1, 1, 1), (255, 255, 255))
        mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
        card[mask == 0] = [0, 0, 0]

        # Fill the blanks
        card = fill_card_void(card)

        if DEBUGGING:
            cv2.imshow("Card", card)
            cv2.waitKey(0)

        card_images.append(card)
    return card_images


def test():
    scan = read_file(TEST_FILE)
    process_scan(scan)

    cv2.waitKey(0)


def main():
    """ Code that separates cards on blue background """

    if DEBUGGING:
        test()
        return

    subdir, dirs, files = next(os.walk(input_path))

    for dir in dirs:
        inp = input_path / dir
        out = output_path / dir

        out.mkdir(parents=True, exist_ok=True)

        i = 0
        for file in os.listdir(inp):
            print(inp / file)
            scan = read_file(inp / file)
            cards = process_scan(scan)

            print(len(cards))
            for card in cards:
                write_file(out / f"{i}.jpg", card)
                i += 1


if __name__ == "__main__":
    main()
