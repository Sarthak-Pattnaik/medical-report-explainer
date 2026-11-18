from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image


# Uncomment and update this path if Tesseract is not
# available through the system PATH on Windows.
#
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )


def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an image using Tesseract OCR.
    """

    image = Image.open(file_path)

    text = pytesseract.image_to_string(image)

    return text.strip()

def extract_pages_from_pdf(file_path: str) -> list[str]:
    """
    Extract text from a text-based PDF, one string per page.
    """

    with pymupdf.open(file_path) as document:
        return [page.get_text() for page in document]


def extract_pages(file_path: str) -> list[str]:
    """
    Extract text page by page. An image counts as one page.
    """

    extension = Path(file_path).suffix.lower()

    if extension in [".jpg", ".jpeg", ".png"]:
        return [extract_text_from_image(file_path)]

    if extension == ".pdf":
        return extract_pages_from_pdf(file_path)

    raise ValueError("Unsupported file type")


def extract_text(file_path: str) -> str:
    """
    Extract the full text as one string.
    """

    return "\n".join(extract_pages(file_path)).strip()