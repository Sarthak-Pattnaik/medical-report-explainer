"""
Text extraction from uploaded reports.

- Text PDFs: PyMuPDF reads the text directly.
- Scanned PDF pages (no text layer): the page is turned into an
  image and read with Tesseract OCR.
- Images: cleaned up (orientation, grayscale, size, contrast)
  and read with Tesseract OCR.
- Pages Tesseract can't read well (usually handwriting) are
  read by a vision model on Groq instead.

Tesseract finds the page's script (Latin, Devanagari, Bengali)
and reads it with English plus that language, when its
language pack is installed.
"""

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import pymupdf
import pytesseract
from PIL import Image, ImageOps, ImageStat

from app.services import vision_ocr_service

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

# A page goes to the vision model when Tesseract's average word
# confidence (0-100) is below MIN_OCR_CONFIDENCE, or when more
# than MAX_LOW_CONFIDENCE_SHARE of its words score below
# LOW_WORD_CONFIDENCE. Clear printed pages average 85+ with
# almost no low-scoring words; handwriting has many.
MIN_OCR_CONFIDENCE = 80
LOW_WORD_CONFIDENCE = 60
MAX_LOW_CONFIDENCE_SHARE = 0.15

# Tesseract's rotation and script guesses are used only when it
# is at least this sure. Blurry pages and handwriting give weak
# guesses, and a wrong rotation ruins the page.
MIN_ORIENTATION_CONFIDENCE = 1.5
MIN_SCRIPT_CONFIDENCE = 1.0

# Most pages per report sent to the vision model. Each page uses
# about 2,000 tokens of its 8,000-tokens-per-minute limit for the
# image alone, so more pages mean longer waits.
MAX_VISION_PAGES = 5

# A page whose brightness varies less than this is blank.
BLANK_PAGE_STDDEV = 5

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

    rotate = int(osd.get("rotate", 0))
    script = osd.get("script")

    if float(osd.get("orientation_conf", 0)) < MIN_ORIENTATION_CONFIDENCE:
        rotate = 0

    if float(osd.get("script_conf", 0)) < MIN_SCRIPT_CONFIDENCE:
        script = None

    return rotate, script


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


class OcrResult(NamedTuple):
    text: str
    # Tesseract's average word confidence, 0-100.
    confidence: float
    words: int
    # Share of words scoring below LOW_WORD_CONFIDENCE.
    low_share: float = 0.0


@dataclass
class ExtractedReport:
    pages: list[str]
    # 1-based numbers of pages read by the vision model.
    vision_pages: list[int] = field(default_factory=list)


def _read_with_confidence(image: Image.Image, lang: str) -> OcrResult:
    """
    Read an image with Tesseract and keep its confidence for
    each word, so that pages it struggles with can be spotted.
    """

    data = pytesseract.image_to_data(
        image,
        lang=lang,
        output_type=pytesseract.Output.DICT,
    )

    lines: dict[tuple, list[str]] = {}
    confidences = []

    for index, word in enumerate(data["text"]):
        word = word.strip()

        if not word:
            continue

        confidence = float(data["conf"][index])

        if confidence >= 0:
            confidences.append(confidence)

        line = (
            data["block_num"][index],
            data["par_num"][index],
            data["line_num"][index],
        )
        lines.setdefault(line, []).append(word)

    text = "\n".join(" ".join(words) for words in lines.values())

    if not confidences:
        return OcrResult(text, 0.0, 0, 0.0)

    average = sum(confidences) / len(confidences)
    low = sum(c < LOW_WORD_CONFIDENCE for c in confidences)

    return OcrResult(text, average, len(confidences), low / len(confidences))


def ocr_image(image: Image.Image) -> tuple[OcrResult, Image.Image]:
    """
    Read text from a prepared image: fix its rotation, then
    read it with the languages that match its script. Returns
    the result and the upright image.
    """

    rotate, script = detect_orientation(image)

    if rotate:
        image = image.rotate(-rotate, expand=True)

    return _read_with_confidence(image, ocr_languages(script)), image


def is_blank(image: Image.Image) -> bool:
    """
    True for an empty page, such as the blank back of a scan.
    """

    return ImageStat.Stat(image.convert("L")).stddev[0] < BLANK_PAGE_STDDEV


def needs_vision(result: OcrResult, image: Image.Image) -> bool:
    """
    True when Tesseract could not read the page well, which
    usually means handwriting or a very poor photo.
    """

    if result.words == 0:
        return not is_blank(image)

    return (
        result.confidence < MIN_OCR_CONFIDENCE
        or result.low_share > MAX_LOW_CONFIDENCE_SHARE
    )


class _VisionBudget:
    """
    Counts pages sent to the vision model for one report.
    """

    def __init__(self):
        self.used = 0

    def take(self) -> bool:
        if not vision_ocr_service.vision_enabled():
            return False

        if self.used >= MAX_VISION_PAGES:
            logger.warning(
                "Vision limit of %d pages reached; using Tesseract text",
                MAX_VISION_PAGES,
            )
            return False

        self.used += 1
        return True


def read_image(image: Image.Image, budget: _VisionBudget) -> tuple[str, bool]:
    """
    Read a prepared image. Pages Tesseract can't read well are
    sent to the vision model. Returns (text, read_by_vision).
    """

    result, upright = ocr_image(image)

    if not needs_vision(result, upright) or not budget.take():
        return result.text, False

    logger.info(
        "Tesseract confidence %.0f on %d words (%.0f%% low); "
        "reading page with the vision model",
        result.confidence,
        result.words,
        result.low_share * 100,
    )

    try:
        text = vision_ocr_service.read_page(upright)
    except Exception:
        logger.exception("Vision model failed; using Tesseract text")
        return result.text, False

    if not text:
        return result.text, False

    return text, True


def pdf_page_image(page: pymupdf.Page) -> Image.Image:
    """
    Turn a scanned PDF page into a grayscale image.
    """

    pixmap = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
    image = Image.frombytes(
        "L",
        (pixmap.width, pixmap.height),
        pixmap.samples,
    )

    return ImageOps.autocontrast(image)


def extract_report_from_pdf(file_path: str) -> ExtractedReport:
    """
    Extract text from a PDF, one string per page. Pages without
    a text layer (scans) are read with OCR.
    """

    report = ExtractedReport(pages=[])
    budget = _VisionBudget()
    ocr_pages = 0

    with pymupdf.open(file_path) as document:
        for number, page in enumerate(document, start=1):
            text = page.get_text()

            if len(text.strip()) >= MIN_PAGE_TEXT_CHARS:
                report.pages.append(text)
                continue

            if ocr_pages >= MAX_OCR_PAGES:
                logger.warning(
                    "Skipping OCR for page %d: limit of %d "
                    "scanned pages reached",
                    number,
                    MAX_OCR_PAGES,
                )
                report.pages.append(text)
                continue

            ocr_pages += 1

            try:
                page_text, by_vision = read_image(pdf_page_image(page), budget)
            except Exception:
                logger.exception("OCR failed for page %d", number)
                report.pages.append(text)
                continue

            report.pages.append(page_text)

            if by_vision:
                report.vision_pages.append(number)

    if ocr_pages:
        logger.info("Read %d scanned PDF page(s) with OCR", ocr_pages)

    return report


def extract_report_from_image(file_path: str) -> ExtractedReport:
    """
    Extract text from an image file.
    """

    with Image.open(file_path) as image:
        text, by_vision = read_image(prepare_image(image), _VisionBudget())

    return ExtractedReport(pages=[text], vision_pages=[1] if by_vision else [])


def extract_report(file_path: str) -> ExtractedReport:
    """
    Extract text page by page, and note which pages were read
    by the vision model. An image counts as one page.
    """

    extension = Path(file_path).suffix.lower()

    if extension in [".jpg", ".jpeg", ".png"]:
        return extract_report_from_image(file_path)

    if extension == ".pdf":
        return extract_report_from_pdf(file_path)

    raise ValueError("Unsupported file type")


def extract_pages(file_path: str) -> list[str]:
    """
    Extract text page by page. An image counts as one page.
    """

    return extract_report(file_path).pages


def extract_text(file_path: str) -> str:
    """
    Extract the full text as one string.
    """

    return "\n".join(extract_pages(file_path)).strip()
