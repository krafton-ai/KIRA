"""
Language Detection Utility

Helper functions to detect text language
"""

import re


def detect_language(text: str) -> str:
    """Detect language by checking for Korean characters

    Args:
        text: Text to analyze

    Returns:
        str: "Korean" or "English"
    """
    if re.search(r'[가-힣]', text):
        return "Korean"
    return "English"
