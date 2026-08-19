"""Preprocessing utilities for OCR and layout analysis.

Functions:
- deskew_image
- denoise_image
- enhance_contrast
- adaptive_binarize

These use OpenCV and PIL. Parameters are configurable.
"""
from typing import Tuple
import cv2
import numpy as np
from PIL import Image, ImageEnhance


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Estimate skew angle and rotate image to deskew.

    Args:
        image: BGR or grayscale image as numpy array.
    Returns:
        deskewed image as numpy array.
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Use threshold to get binary image
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Invert colors: text as white
    bw = 255 - bw

    coords = np.column_stack(np.where(bw > 0))
    if coords.size == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed


def denoise_image(image: np.ndarray, h: int = 10) -> np.ndarray:
    """Apply non-local means denoising (good for scanned documents).

    Args:
        image: BGR or grayscale numpy array
        h: parameter controlling filter strength
    Returns:
        denoised image
    """
    if len(image.shape) == 3:
        den = cv2.fastNlMeansDenoisingColored(image, None, h, h, 7, 21)
    else:
        den = cv2.fastNlMeansDenoising(image, None, h, 7, 21)
    return den


def enhance_contrast_pil(image: np.ndarray, factor: float = 1.5) -> np.ndarray:
    """Enhance contrast using PIL for subtle improvements."""
    if len(image.shape) == 3:
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        img = Image.fromarray(image)
    enhancer = ImageEnhance.Contrast(img)
    enhanced = enhancer.enhance(factor)
    arr = np.array(enhanced)
    if len(image.shape) == 3:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return arr


def adaptive_binarize(image: np.ndarray, block_size: int = 35, C: int = 10) -> np.ndarray:
    """Adaptive thresholding useful for uneven illumination."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    bin_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, block_size, C)
    return bin_img
