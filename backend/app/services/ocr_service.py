"""
Text extraction from uploaded reports.

- Text PDFs: PyMuPDF reads the text directly.
- Scanned PDF pages (no text layer): the page is turned into an
  image and read with Tesseract OCR.
- Images: cleaned up (orientation, grayscale, size, contrast)
  and read with Tesseract OCR.

Tesseract finds the page's script (Latin, Devanagari, Bengali)
and reads it with English plus that language, when its
language pack is installed.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Uncomment and update this path if Tesseract is not
# available through the system PATH on Windows.
#
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )

# A PDF page with less text than this is treated as scanned.
MIN_PAGE_TEXT_CHARS = 20

# Resolution used to turn a scanned PDF page into an image.
# Tesseract works best at about 300 DPI.
SCAN_DPI = 300

# Most scanned pages read per report, to bound processing time.
MAX_OCR_PAGES = 40

# Small images are enlarged to about this width before OCR,
# at most this many times.
TARGET_IMAGE_WIDTH = 1800
MAX_UPSCALE = 3.0

# Tesseract script name -> language pack. English is always
# added, because Indian reports usually mix English with the
# local language.
SCRIPT_LANGUAGES = {
    "Devanagari": "hin",
    "Bengali": "ben",
}

# Optional limit on the language packs used, e.g. "eng+hin".
# Empty means every installed pack from SCRIPT_LANGUAGES.
OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "")


@lru_cache(maxsize=1)
def installed_languages() -> frozenset[str]:
    """
    Language packs Tesseract has on this machine.
    """

    try:
        return frozenset(pytesseract.get_languages(config=""))
    except Exception:
        logger.exception("Could not list Tesseract languages")
        return frozenset({"eng"})


def ocr_languages(script: str | None) -> str:
    """
    Tesseract language string for a script, for example
    "eng+hin". When the script is unknown (too little text to
    tell), every available Indian language pack is added.
    Missing language packs are skipped.
    """

    installed = installed_languages()
    allowed = set(OCR_LANGUAGES.split("+")) if OCR_LANGUAGES else None

    def available(language: str) -> bool:
        return language in installed and (
            allowed is None or language in allowed
        )

    if script is None:
        extras = [
            language
            for language in SCRIPT_LANGUAGES.values()
            if available(language)
        ]
        return "+".join(["eng", *extras])

    extra = SCRIPT_LANGUAGES.get(script)

    if extra is None:
        return "eng"

    if not available(extra):
        logger.warning(
            "Tesseract language pack '%s' is not available; "
            "reading %s text as English",
            extra,
            script,
        )
        return "eng"

    return f"eng+{extra}"


def detect_orientation(image: Image.Image) -> tuple[int, str | None]:
    """
    Ask Tesseract how far the page is rotated and which script
    it uses. Returns (0, None) when it can't tell, for example
    when there is very little text.
    """

    if "osd" not in installed_languages():
        return 0, None

    try:
        osd = pytesseract.image_to_osd(
            image,
            output_type=pytesseract.Output.DICT,
        )
    except pytesseract.TesseractError:
        return 0, None

    return int(osd.get("rotate", 0)), osd.get("script")


def prepare_image(image: Image.Image) -> Image.Image:
    """
    Clean up a photo or scan before OCR: apply the camera's
    rotation, make it grayscale, enlarge it if small and
    stretch the contrast.
    """

    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    if image.width < TARGET_IMAGE_WIDTH:
        scale = min(TARGET_IMAGE_WIDTH / image.width, MAX_UPSCALE)
        image = image.resize(
            (round(image.width * scale), round(image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    return ImageOps.autocontrast(image)


def ocr_image(image: Image.Image) -> str:
    """
    Read text from a prepared image: fix its rotation, then
    read it with the languages that match its script.
    """

    rotate, script = detect_orientation(image)

    if rotate:
        image = image.rotate(-rotate, expand=True)

    text = pytesseract.image_to_string(
        image,
        lang=ocr_languages(script),
    )

    return text.strip()


def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an image file.
    """

    with Image.open(file_path) as image:
        return ocr_image(prepare_image(image))


def ocr_pdf_page(page: pymupdf.Page) -> str:
    """
    Turn a scanned PDF page into a grayscale image and read it.
    """

    pixmap = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
    image = Image.frombytes(
        "L",
        (pixmap.width, pixmap.height),
        pixmap.samples,
    )

    return ocr_image(ImageOps.autocontrast(image))


def extract_pages_from_pdf(file_path: str) -> list[str]:
    """
    Extract text from a PDF, one string per page. Pages without
    a text layer (scans) are read with OCR.
    """

    pages = []
    ocr_pages = 0

    with pymupdf.open(file_path) as document:
        for number, page in enumerate(document, start=1):
            text = page.get_text()

            if len(text.strip()) >= MIN_PAGE_TEXT_CHARS:
                pages.append(text)
                continue

            if ocr_pages >= MAX_OCR_PAGES:
                logger.warning(
                    "Skipping OCR for page %d: limit of %d "
                    "scanned pages reached",
                    number,
                    MAX_OCR_PAGES,
                )
                pages.append(text)
                continue

            ocr_pages += 1

            try:
                pages.append(ocr_pdf_page(page))
            except Exception:
                logger.exception("OCR failed for page %d", number)
                pages.append(text)

    if ocr_pages:
        logger.info("Read %d scanned PDF page(s) with OCR", ocr_pages)

    return pages


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
