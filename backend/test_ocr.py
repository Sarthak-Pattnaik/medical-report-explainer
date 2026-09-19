from app.services.ocr_service import extract_text


file_path = "storage/uploads/exemplar_medical_report.pdf"  # Replace with the path to your test file

text = extract_text(file_path)

print("Extracted Text:")
print(text)