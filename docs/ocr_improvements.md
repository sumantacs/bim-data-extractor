# OCR & Layout improvements

This document describes the new OCR preprocessing, engine integration, and layout helpers added in the `improve-ocr-layout-parsing` branch.

Files added:
- ocr/preprocessing.py: deskew, denoise, contrast enhancement, adaptive binarization.
- ocr/ocr_engines.py: wrappers for pytesseract, easyocr, and placeholder for Google Vision.
- ocr/layout.py: text block detection and line detection for dimension clues.
- ocr/schema.py: dataclass for extracted fields including confidence and bounding polygon.
- tests/test_ocr_pipeline.py: basic smoke tests.

How to use
1. Install dependencies: OpenCV, pytesseract, easyocr (optional), pillow.

pip install opencv-python pytesseract easyocr pillow

2. Example pipeline (high-level):

- Load image with OpenCV
- deskew_image -> denoise_image -> enhance_contrast_pil -> adaptive_binarize
- Run one or more OCR engines (tesseract/easyocr)
- Run layout.detect_text_blocks and layout.detect_dimension_lines
- Convert engine outputs to ocr.schema.ExtractedField with confidence and polygon

Evaluation
- Add a labeled dataset (30+ scanned pages) under data/eval and provide a CSV of ground-truth fields.
- Write evaluation scripts to compute precision/recall per field and measure baseline.

Next steps
- Implement Google Vision wrapper (requires credentials) and batch upload for high-res pages.
- Add rotated-text-specific detection using MSER or OCR rotation via sliding windows.
- Add unit/integration tests against a small labeled PNG sample.
