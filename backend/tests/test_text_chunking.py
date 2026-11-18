from app.services.text_chunking import (
    estimate_tokens,
    split_into_chunks,
    strip_repeated_lines,
)

HEADER = "City Diagnostics Lab, 12 Main Road, Bhubaneswar"
FOOTER = "This report is for the referring doctor only."


def make_page(body: str) -> str:
    return f"{HEADER}\n{body}\n{FOOTER}"


def test_short_report_is_unchanged():
    pages = [make_page("Haemoglobin 11.8"), make_page("Ferritin 18")]

    assert strip_repeated_lines(pages) == pages


def test_repeated_header_and_footer_kept_once():
    pages = [make_page(f"Test {i} 5.0") for i in range(4)]

    cleaned = strip_repeated_lines(pages)
    text = "\n".join(cleaned)

    assert text.count(HEADER) == 1
    assert text.count(FOOTER) == 1
    for i in range(4):
        assert f"Test {i} 5.0" in text


def test_short_repeated_lines_are_kept():
    pages = [f"Test {i}\n5.0\ng/dL" for i in range(4)]

    cleaned = strip_repeated_lines(pages)

    assert all("g/dL" in page for page in cleaned)


def test_line_on_few_pages_is_kept():
    note = "Sample received in a haemolysed condition"
    pages = [make_page("A 1"), make_page(note), make_page("B 2"), make_page("C 3")]

    cleaned = strip_repeated_lines(pages)

    assert note in cleaned[1]


def test_chunks_respect_limit_and_keep_pages_whole():
    pages = [f"Page {i}\n" + "x" * 40 for i in range(10)]

    chunks = split_into_chunks(pages, max_chars=120)

    assert all(len(chunk) <= 120 for chunk in chunks)
    for i in range(10):
        assert sum(f"Page {i}\n" in chunk for chunk in chunks) == 1


def test_long_page_is_split_by_lines():
    page = "\n".join(f"Line {i} " + "y" * 20 for i in range(20))

    chunks = split_into_chunks([page], max_chars=100)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert "\n".join(chunks).count("Line ") == 20


def test_empty_pages_make_no_chunks():
    assert split_into_chunks(["", "   ", "\n"]) == []


def test_estimate_tokens():
    assert estimate_tokens("a" * 400) == 100