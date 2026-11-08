from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000
    )

    # IANA timezone name from the browser, e.g. "Asia/Kolkata".
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty")

        return value