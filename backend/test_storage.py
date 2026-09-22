from app.services.storage_service import StorageService


storage = StorageService()

response = storage.upload_file(
    file_path="test_storage.pdf",
    storage_path="test/test_storage.pdf",
    content_type="application/pdf",
)

print("Upload successful:")
print(response)