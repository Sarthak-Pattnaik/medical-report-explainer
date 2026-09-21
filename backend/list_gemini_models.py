from dotenv import load_dotenv

load_dotenv()

import os

from google import genai


def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=api_key
    )

    for model in client.models.list():
        name = model.name or ""

        if "generateContent" in str(
            model.supported_actions
        ):
            print(name)


if __name__ == "__main__":
    main()