"""Layout analysis helpers: detect text blocks, lines (for dimensions), and basic leader detection.
"""
from typing import List, Tuple
import numpy as np
import cv2


def detect_text_blocks(image: np.ndarray, min_area: int = 100) -> List[Tuple[int,int,int,int]]:
    """Return list of bounding boxes (x,y,w,h) for candidate text blocks using morphology and contours."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    # Binarize
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Invert (text white)
    bw = 255 - bw
    # Morphological close to merge text lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= min_area:
            boxes.append((x, y, w, h))
    return boxes


def detect_dimension_lines(image: np.ndarray, min_length: int = 50) -> List[Tuple[int,int,int,int]]:
    """Detect straight lines (potential dimension or extension lines) using probabilistic Hough.

    Returns lines as (x1,y1,x2,y2).
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=min_length, maxLineGap=10)
    out = []
    if lines is None:
        return out
    for l in lines:
        x1, y1, x2, y2 = l[0]
        out.append((x1, y1, x2, y2))
    return out


def polygon_from_bbox(x:int,y:int,w:int,h:int):
    return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
