import base64
import io
from types import SimpleNamespace

from PIL import Image

from app.services import vision_ocr_service as vision


class FakeClient:
    def __init__(self, reply):
        self.requests = []
        self.reply = reply
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self.create)
        )

    def create(self, **request):
        self.requests.append(request)
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_large_image_is_shrunk_and_sent_as_jpeg():
    url = vision._image_data_url(Image.new("RGB", (4000, 3000), "white"))

    assert url.startswith("data:image/jpeg;base64,")
    data = base64.b64decode(url.split(",", 1)[1])
    image = Image.open(io.BytesIO(data))
    assert max(image.size) == vision.MAX_IMAGE_SIDE


def test_read_page_sends_image_and_strict_prompt(monkeypatch):
    client = FakeClient("  Hb 11.8 g/dL\nFBS [unclear] mg/dL  ")
    monkeypatch.setattr(vision, "_client", client)

    text = vision.read_page(Image.new("L", (800, 600), "white"))

    assert text == "Hb 11.8 g/dL\nFBS [unclear] mg/dL"
    request = client.requests[0]
    prompt, image = request["messages"][0]["content"]
    assert "[unclear]" in prompt["text"]
    assert image["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert request["model"] == vision.VISION_MODEL
    assert request["reasoning_effort"] == "none"
    assert request["temperature"] == 0


def test_empty_answer_is_empty_text(monkeypatch):
    monkeypatch.setattr(vision, "_client", FakeClient(None))

    assert vision.read_page(Image.new("L", (100, 100))) == ""


def test_vision_needs_a_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    assert vision.vision_enabled() is False
