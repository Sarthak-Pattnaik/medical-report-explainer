"""
Reads a page image with a vision model on Groq. Used for pages
Tesseract can't read well, usually handwriting.

The model is told to copy text exactly and to write [unclear]
instead of guessing, because a misread number or medicine name
on a medical report is dangerous.
"""

import base64
import io
import logging
import os

from dotenv import load_dotenv
from groq import Groq
from PIL import Image

load_dotenv()

logger = logging.getLogger(__name__)

VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")

# Set VISION_OCR_ENABLED=false to read every page with Tesseract.
VISION_OCR_ENABLED = os.getenv("VISION_OCR_ENABLED", "true").lower() != "false"

# Longest image side sent to the model. Big enough for small
# handwriting, small enough to keep the upload light.
MAX_IMAGE_SIDE = 2000
JPEG_QUALITY = 85

# Room for the page text. The image itself costs about 2,000
# tokens, so one page stays well under the 8,000 limit.
MAX_COMPLETION_TOKENS = 2500

UNCLEAR = "[unclear]"

PROMPT = f"""
You are reading one page of a medical report or prescription.
Some or all of it may be handwritten.

Write out all the text on the page exactly as written.

Rules:
1. Copy numbers, units, dates, names and medicine names exactly.
   Do not correct, complete or guess anything.
2. If a word or number cannot be read with confidence, write
   {UNCLEAR} in its place.
3. Keep each line of the page on its own line. For tables, keep
   each row on one line with its columns in order.
4. Return only the page text: no headings, comments or
   explanations.
5. If the page has no text, return nothing.
""".strip()


def vision_enabled() -> bool:
    return VISION_OCR_ENABLED and bool(os.getenv("GROQ_API_KEY"))


def _image_data_url(image: Image.Image) -> str:
    """
    Shrink the image if needed and encode it as a JPEG data URL.
    """

    image = image.convert("L")
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    return f"data:image/jpeg;base64,{encoded}"


_client = None


def _get_client() -> Groq:
    global _client

    if _client is None:
        # The default retries wait out a rate limit (429) when a
        # report has several handwritten pages.
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    return _client


def read_page(image: Image.Image) -> str:
    """
    Return the text on the page, as read by the vision model.
    """

    completion = _get_client().chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": _image_data_url(image)},
                    },
                ],
            }
        ],
        temperature=0,
        # Plain reading needs no step-by-step reasoning.
        reasoning_effort="none",
        max_completion_tokens=MAX_COMPLETION_TOKENS,
    )

    text = (completion.choices[0].message.content or "").strip()

    logger.info(
        "Vision model read %d characters (%d marked unclear)",
        len(text),
        text.count(UNCLEAR),
    )

    return text
