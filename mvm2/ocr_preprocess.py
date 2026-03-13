import cv2
import numpy as np
import easyocr

# Global OCR reader (English)
_reader = easyocr.Reader(["en"], gpu=False)

def preprocess_image(image_path):
    """Gaussian blur + adaptive threshold."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image at path: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.2)
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )
    return thresh

def run_ocr(image_path):
    """OCR: tokens + confidences + average."""
    results = _reader.readtext(image_path, detail=1)

    tokens = []
    confidences = []

    for bbox, text, conf in results:
        if text.strip():
            tokens.append(text.strip())
            confidences.append(float(conf))

    if confidences:
        ocr_conf = sum(confidences) / len(confidences)
    else:
        ocr_conf = 0.0

    return {
        "tokens": tokens,
        "confidences": confidences,
        "ocr_conf": ocr_conf,
    }
