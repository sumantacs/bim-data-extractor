"""Wrappers for OCR engines: Tesseract, EasyOCR, and placeholder for Google Vision.

Each function returns a list of dicts: {text, confidence, bbox}
Where bbox is (x, y, w, h) or polygon.
"""
from typing import List, Dict, Tuple
import numpy as np

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    import easyocr
except Exception:
    easyocr = None


def ocr_tesseract(image: np.ndarray, lang: str = 'eng') -> List[Dict]:
    """Run Tesseract OCR and return detections.

    Requires pytesseract to be installed and Tesseract binary available on PATH.
    """
    if pytesseract is None:
        raise RuntimeError('pytesseract not installed')

    config = '--psm 6'  # assume a block of text; tune as needed
    data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
    results = []
    n = len(data['text'])
    for i in range(n):
        text = data['text'][i].strip()
        if text == "":
            continue
        conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0.0
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        results.append({'text': text, 'confidence': conf / 100.0, 'bbox': (x, y, w, h)})
    return results


def ocr_easyocr(image: np.ndarray, langs: List[str] = ['en']) -> List[Dict]:
    if easyocr is None:
        raise RuntimeError('easyocr not installed')
    reader = easyocr.Reader(langs, gpu=False)
    raw = reader.readtext(image)
    results = []
    for bbox, text, conf in raw:
        # bbox is list of 4 points
        results.append({'text': text, 'confidence': float(conf), 'bbox': bbox})
    return results


def ocr_google_vision(image_bytes: bytes, credentials_json: str = None) -> List[Dict]:
    """Placeholder for Google Vision OCR integration.

    Notes: The real implementation should use google-cloud-vision client, pass credentials, and parse responses.
    """
    raise NotImplementedError('Google Vision OCR wrapper needs implementation and API credentials')
