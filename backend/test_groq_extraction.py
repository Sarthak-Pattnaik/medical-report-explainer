from app.services.groq_extraction_service import (
    GroqExtractionService,
)


def main():
    report_text = """
    Complete Blood Count

    Hemoglobin: 11.2 g/dL
    Reference Range: 12.0-15.5 g/dL
    Status: Low

    White Blood Cell Count: 7200 /uL
    Status: Normal
    """

    service = GroqExtractionService()

    result = service.extract(
        report_text
    )

    print(
        result.model_dump_json(indent=2)
    )


if __name__ == "__main__":
    main()