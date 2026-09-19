from app.services.ocr_service import extract_text
from app.services.structured_extraction_service import (
    extract_structured_data,
)


file_path = "storage/uploads/cc168ce4-b996-40d6-9d73-3811d10692f7.pdf"

text = extract_text(file_path)

structured_data = extract_structured_data(text)

print("Structured Data:")

for parameter, data in structured_data.items():
    print(f"{parameter}: {data}")