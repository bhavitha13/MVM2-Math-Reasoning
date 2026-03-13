def build_representation(ocr_tokens):
    """
    Representation service: turns raw OCR tokens into clean problem text.
    """
    problem_text = " ".join(ocr_tokens)
    return {
        "problem_text": problem_text,
        "latex": None,
    }
