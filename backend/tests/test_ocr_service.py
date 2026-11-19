"""
OCR tests. Tesseract itself is not installed in CI, so its calls
are replaced with fakes; these tests check our own logic.
"""

import pymupdf
import pytesseract
import pytest
from PIL import Image

from app.services import ocr_service as ocr


def use_languages(monkeypatch, *languages):
    monkeypatch.setattr(
        ocr, "installed_languages", lambda: frozenset(languages)
    )


# ---------- Languages ----------

def test_script_adds_its_language(monkeypatch):
    use_languages(monkeypatch, "eng", "hin", "ben", "osd")

    assert ocr.ocr_languages("Devanagari") == "eng+hin"
    assert ocr.ocr_languages("Bengali") == "eng+ben"
    assert ocr.ocr_languages("Latin") == "eng"


def test_missing_language_pack_falls_back_to_english(monkeypatch):
    use_languages(monkeypatch, "eng", "osd")

    assert ocr.ocr_languages("Bengali") == "eng"


def test_unknown_script_uses_every_installed_indian_pack(monkeypatch):
    use_languages(monkeypatch, "eng", "hin", "ben")

    assert ocr.ocr_languages(None) == "eng+hin+ben"


def test_language_setting_limits_packs(monkeypatch):
    use_languages(monkeypatch, "eng", "hin", "ben")
    monkeypatch.setattr(ocr, "OCR_LANGUAGES", "eng+hin")

    assert ocr.ocr_languages("Bengali") == "eng"
    assert ocr.ocr_languages(None) == "eng+hin"


# ---------- Orientation ----------

def test_no_orientation_data_means_no_rotation(monkeypatch):
    use_languages(monkeypatch, "eng")

    assert ocr.detect_orientation(Image.new("L", (10, 10))) == (0, None)


def test_too_little_text_means_no_rotation(monkeypatch):
    use_languages(monkeypatch, "eng", "osd")

    def fail(*args, **kwargs):
        raise pytesseract.TesseractError(1, "Too few characters")

    monkeypatch.setattr(ocr.pytesseract, "image_to_osd", fail)

    assert ocr.detect_orientation(Image.new("L", (10, 10))) == (0, None)


def test_rotated_page_is_turned_upright(monkeypatch):
    use_languages(monkeypatch, "eng", "hin")
    monkeypatch.setattr(
        ocr, "detect_orientation", lambda image: (90, "Devanagari")
    )
    seen = {}

    def fake_ocr(image, lang):
        seen["size"] = image.size
        seen["lang"] = lang
        return " text "

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_ocr)

    text = ocr.ocr_image(Image.new("L", (200, 100)))

    assert text == "text"
    assert seen == {"size": (100, 200), "lang": "eng+hin"}


# ---------- Image clean-up ----------

def test_small_image_is_enlarged_and_made_grayscale():
    image = ocr.prepare_image(Image.new("RGB", (300, 200), "white"))

    assert image.mode == "L"
    assert image.size == (900, 600)  # at most 3 times


def test_large_image_keeps_its_size():
    image = ocr.prepare_image(Image.new("RGB", (2400, 3000), "white"))

    assert image.size == (2400, 3000)


# ---------- PDFs ----------

def make_pdf(path, pages):
    """
    pages: list of strings. A string becomes a text page;
    None becomes a page with no text layer, like a scan.
    """

    document = pymupdf.open()

    for text in pages:
        page = document.new_page()

        if text:
            page.insert_text((72, 72), text)

    document.save(path)
    document.close()


@pytest.fixture
def fake_page_ocr(monkeypatch):
    calls = []

    def fake(image):
        calls.append(image.size)
        return f"OCR page {len(calls)}"

    monkeypatch.setattr(ocr, "ocr_image", fake)
    return calls


def test_text_pages_are_read_directly(tmp_path, fake_page_ocr):
    path = tmp_path / "report.pdf"
    make_pdf(path, ["Haemoglobin 11.8 g/dL 13.0 - 17.0"])

    pages = ocr.extract_pages(str(path))

    assert "Haemoglobin 11.8" in pages[0]
    assert fake_page_ocr == []


def test_scanned_pages_are_read_with_ocr(tmp_path, fake_page_ocr):
    path = tmp_path / "report.pdf"
    make_pdf(path, ["Haemoglobin 11.8 g/dL 13.0 - 17.0", None])

    pages = ocr.extract_pages(str(path))

    assert "Haemoglobin 11.8" in pages[0]
    assert pages[1] == "OCR page 1"
    assert len(fake_page_ocr) == 1


def test_ocr_page_limit(tmp_path, fake_page_ocr, monkeypatch):
    monkeypatch.setattr(ocr, "MAX_OCR_PAGES", 1)
    path = tmp_path / "report.pdf"
    make_pdf(path, [None, None])

    pages = ocr.extract_pages(str(path))

    assert pages[0] == "OCR page 1"
    assert pages[1].strip() == ""
    assert len(fake_page_ocr) == 1


def test_failed_page_does_not_stop_the_report(tmp_path, monkeypatch):
    def broken(image):
        raise RuntimeError("tesseract crashed")

    monkeypatch.setattr(ocr, "ocr_image", broken)
    path = tmp_path / "report.pdf"
    make_pdf(path, [None, "Ferritin 18 ng/mL 30 - 400"])

    pages = ocr.extract_pages(str(path))

    assert len(pages) == 2
    assert "Ferritin 18" in pages[1]


def test_unsupported_file_type():
    with pytest.raises(ValueError):
        ocr.extract_pages("report.docx")
