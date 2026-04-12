"""Eight-step text cleaning pipeline (order is significant)."""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Apply the handbook cleaning pipeline from INSTRUCTIONS.md §1.2 in fixed order.

    Does not lowercase, strip punctuation globally, or remove numeric content.

    Args:
        text: Raw or partially normalized text from PDF extraction.

    Returns:
        Cleaned text suitable for sentence tokenization and chunking.
    """
    if not text:
        return ""

    # 1. Fix encoding
    t = text.encode("utf-8", errors="ignore").decode("utf-8")

    # 2. Normalize unicode (compatibility decomposition + composition)
    t = unicodedata.normalize("NFKC", t)

    # 3. Remove hyphenation at line breaks
    t = re.sub(r"-\n", "", t)

    # 4. Rejoin soft line breaks (single newline → space; paragraphs preserved)
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)

    # 5. Strip common handbook headers/footers (NUST … Handbook … year/page)
    t = re.sub(r"NUST\s+.*?Handbook.*?\d+", " ", t, flags=re.IGNORECASE | re.DOTALL)

    # 6. Remove page-number-only lines
    t = re.sub(r"^\s*\d+\s*$", "", t, flags=re.MULTILINE)

    # 7. Collapse horizontal whitespace
    t = re.sub(r"[ \t]+", " ", t)

    # 8. Strip leading/trailing whitespace per paragraph
    paragraphs = [p.strip() for p in t.split("\n\n")]
    t = "\n\n".join(p for p in paragraphs if p)

    return t.strip()
