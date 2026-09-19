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


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a text-based PDF using PyMuPDF.
    """

    document = pymupdf.open(file_path) 

    extracted_text = []

    for page in document:
        text = page.get_text()
        extracted_text.append(text)

    document.close()

    return "\n".join(extracted_text).strip()


def extract_text(file_path: str) -> str:
    """
    Extract text based on the file extension.
    """

    path = Path(file_path)

    extension = path.suffix.lower()

    if extension in [".jpg", ".jpeg", ".png"]:
        return extract_text_from_image(file_path)

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    raise ValueError("Unsupported file type")