"""Basic tests for OCR preprocessing pipeline. These are smoke tests that ensure functions run without error.
"""
import numpy as np
import cv2

from ocr import preprocessing, layout


def test_preprocessing_smoke():
    # create a blank image with some text using OpenCV
    img = np.ones((200, 400), dtype='uint8') * 255
    cv2.putText(img, 'DIM 100', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,), 2, cv2.LINE_AA)
    # convert to BGR
    img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    d = preprocessing.deskew_image(img_bgr)
    assert d is not None
    dn = preprocessing.denoise_image(d)
    assert dn is not None
    be = preprocessing.enhance_contrast_pil(dn)
    assert be is not None
    bin_img = preprocessing.adaptive_binarize(be)
    assert bin_img is not None


def test_layout_detection_smoke():
    img = np.ones((200, 400), dtype='uint8') * 255
    cv2.putText(img, 'ROOM A', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,), 2, cv2.LINE_AA)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    boxes = layout.detect_text_blocks(img_bgr)
    assert isinstance(boxes, list)

