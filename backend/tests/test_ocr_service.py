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


def fake_osd(rotate, orientation_conf, script="Latin", script_conf=5.0):
    return lambda image, output_type: {
        "rotate": rotate,
        "orientation_conf": orientation_conf,
        "script": script,
        "script_conf": script_conf,
    }


def test_weak_rotation_guess_is_ignored(monkeypatch):
    use_languages(monkeypatch, "eng", "osd")
    monkeypatch.setattr(ocr.pytesseract, "image_to_osd", fake_osd(180, 0.7))

    assert ocr.detect_orientation(Image.new("L", (10, 10))) == (0, "Latin")


def test_weak_script_guess_is_ignored(monkeypatch):
    use_languages(monkeypatch, "eng", "osd")
    monkeypatch.setattr(
        ocr.pytesseract,
        "image_to_osd",
        fake_osd(90, 5.0, script="Japanese", script_conf=0.1),
    )

    assert ocr.detect_orientation(Image.new("L", (10, 10))) == (90, None)


def tesseract_data(words):
    """
    Fake image_to_data output. words: list of (text, confidence, line).
    """

    return {
        "text": [w for w, _, _ in words],
        "conf": [c for _, c, _ in words],
        "block_num": [1] * len(words),
        "par_num": [1] * len(words),
        "line_num": [line for _, _, line in words],
    }


def test_rotated_page_is_turned_upright(monkeypatch):
    use_languages(monkeypatch, "eng", "hin")
    monkeypatch.setattr(
        ocr, "detect_orientation", lambda image: (90, "Devanagari")
    )
    seen = {}

    def fake_data(image, lang, output_type):
        seen["size"] = image.size
        seen["lang"] = lang
        return tesseract_data(
            [("Hb", 95, 1), ("11.8", 90, 1), ("", -1, 1), ("FBS", 50, 2)]
        )

    monkeypatch.setattr(ocr.pytesseract, "image_to_data", fake_data)

    result, upright = ocr.ocr_image(Image.new("L", (200, 100)))

    assert result.text == "Hb 11.8\nFBS"
    assert result.words == 3
    assert round(result.confidence) == 78
    assert round(result.low_share, 2) == 0.33
    assert upright.size == (100, 200)
    assert seen == {"size": (100, 200), "lang": "eng+hin"}


# ---------- When to use the vision model ----------

TEXT_IMAGE = Image.new("L", (50, 50), "white")
TEXT_IMAGE.paste(0, (10, 10, 40, 20))  # something on the page
BLANK_IMAGE = Image.new("L", (50, 50), "white")


def test_clear_print_stays_with_tesseract():
    result = ocr.OcrResult("text", 92.0, 40, 0.02)

    assert ocr.needs_vision(result, TEXT_IMAGE) is False


def test_low_confidence_goes_to_vision():
    assert ocr.needs_vision(ocr.OcrResult("x", 55.0, 30, 0.5), TEXT_IMAGE)


def test_many_low_words_go_to_vision_even_with_good_average():
    # Neat handwriting: decent average, but many unsure words.
    assert ocr.needs_vision(ocr.OcrResult("x", 83.0, 24, 0.17), TEXT_IMAGE)


def test_no_words_on_a_page_with_marks_goes_to_vision():
    assert ocr.needs_vision(ocr.OcrResult("", 0.0, 0), TEXT_IMAGE)


def test_blank_page_is_not_sent():
    assert not ocr.needs_vision(ocr.OcrResult("", 0.0, 0), BLANK_IMAGE)


@pytest.fixture
def vision(monkeypatch):
    """
    Fake vision model. Set .reply to a string or an exception.
    """

    state = type("Vision", (), {"calls": 0, "reply": "Hb 11.8 g/dL"})()

    def fake_read_page(image):
        state.calls += 1
        if isinstance(state.reply, Exception):
            raise state.reply
        return state.reply

    monkeypatch.setattr(ocr.vision_ocr_service, "vision_enabled", lambda: True)
    monkeypatch.setattr(ocr.vision_ocr_service, "read_page", fake_read_page)
    return state


def use_tesseract_result(monkeypatch, result):
    monkeypatch.setattr(ocr, "ocr_image", lambda image: (result, image))


HANDWRITTEN = ocr.OcrResult("Hb 4. g/AL", 50.0, 20, 0.5)
PRINTED = ocr.OcrResult("Hb 11.8 g/dL", 93.0, 20, 0.0)


def test_handwritten_page_is_read_by_vision(monkeypatch, vision):
    use_tesseract_result(monkeypatch, HANDWRITTEN)

    text, by_vision = ocr.read_image(TEXT_IMAGE, ocr._VisionBudget())

    assert (text, by_vision) == ("Hb 11.8 g/dL", True)


def test_printed_page_does_not_call_vision(monkeypatch, vision):
    use_tesseract_result(monkeypatch, PRINTED)

    text, by_vision = ocr.read_image(TEXT_IMAGE, ocr._VisionBudget())

    assert (text, by_vision) == ("Hb 11.8 g/dL", False)
    assert vision.calls == 0


def test_vision_failure_keeps_tesseract_text(monkeypatch, vision):
    vision.reply = RuntimeError("model removed")
    use_tesseract_result(monkeypatch, HANDWRITTEN)

    text, by_vision = ocr.read_image(TEXT_IMAGE, ocr._VisionBudget())

    assert (text, by_vision) == ("Hb 4. g/AL", False)


def test_empty_vision_answer_keeps_tesseract_text(monkeypatch, vision):
    vision.reply = ""
    use_tesseract_result(monkeypatch, HANDWRITTEN)

    assert ocr.read_image(TEXT_IMAGE, ocr._VisionBudget()) == ("Hb 4. g/AL", False)


def test_vision_off_keeps_tesseract_text(monkeypatch, vision):
    monkeypatch.setattr(ocr.vision_ocr_service, "vision_enabled", lambda: False)
    use_tesseract_result(monkeypatch, HANDWRITTEN)

    assert ocr.read_image(TEXT_IMAGE, ocr._VisionBudget()) == ("Hb 4. g/AL", False)
    assert vision.calls == 0


def test_vision_page_limit(monkeypatch, vision):
    monkeypatch.setattr(ocr, "MAX_VISION_PAGES", 1)
    use_tesseract_result(monkeypatch, HANDWRITTEN)
    budget = ocr._VisionBudget()

    first = ocr.read_image(TEXT_IMAGE, budget)
    second = ocr.read_image(TEXT_IMAGE, budget)

    assert first[1] is True
    assert second == ("Hb 4. g/AL", False)
    assert vision.calls == 1


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

    def fake(image, budget):
        calls.append(image.size)
        return f"OCR page {len(calls)}", False

    monkeypatch.setattr(ocr, "read_image", fake)
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
    def broken(image, budget):
        raise RuntimeError("tesseract crashed")

    monkeypatch.setattr(ocr, "read_image", broken)
    path = tmp_path / "report.pdf"
    make_pdf(path, [None, "Ferritin 18 ng/mL 30 - 400"])

    pages = ocr.extract_pages(str(path))

    assert len(pages) == 2
    assert "Ferritin 18" in pages[1]


def test_unsupported_file_type():
    with pytest.raises(ValueError):
        ocr.extract_pages("report.docx")


def test_pdf_reports_which_pages_used_vision(tmp_path, monkeypatch):
    replies = iter([("printed", False), ("handwritten", True)])
    monkeypatch.setattr(ocr, "read_image", lambda image, budget: next(replies))
    path = tmp_path / "report.pdf"
    make_pdf(path, ["Ferritin 18 ng/mL 30 - 400", None, None])

    report = ocr.extract_report(str(path))

    assert report.pages[1:] == ["printed", "handwritten"]
    assert report.vision_pages == [3]
