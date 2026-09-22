import os
import tempfile

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class StorageService:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        bucket_name = os.getenv(
            "SUPABASE_STORAGE_BUCKET",
            "medical-reports",
        )

        if not supabase_url:
            raise ValueError(
                "SUPABASE_URL is not configured."
            )

        if not service_role_key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY is not configured."
            )

        self.bucket_name = bucket_name

        self.client: Client = create_client(
            supabase_url,
            service_role_key,
        )

    def upload_file(
        self,
        file_path: str,
        storage_path: str,
        content_type: str,
    ):
        with open(file_path, "rb") as file:
            return (
                self.client.storage
                .from_(self.bucket_name)
                .upload(
                    path=storage_path,
                    file=file,
                    file_options={
                        "content-type": content_type,
                        "upsert": "false",
                    },
                )
            )

    def download_file(
        self,
        storage_path: str,
    ):
        return (
            self.client.storage
            .from_(self.bucket_name)
            .download(storage_path)
        )

    def download_to_temp(
        self,
        storage_path: str,
        suffix: str = "",
    ) -> str:
        data = self.download_file(storage_path)

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        )

        try:
            temp_file.write(data)
            temp_file.close()
            return temp_file.name

        except Exception:
            temp_file.close()

            try:
                os.unlink(temp_file.name)
            except OSError:
                pass

            raise

    def delete_file(
        self,
        storage_path: str,
    ):
        return (
            self.client.storage
            .from_(self.bucket_name)
            .remove([storage_path])
        )

    def upload_bytes(
    self,
    file_data: bytes,
    storage_path: str,
    content_type: str
):
        return (
        self.client.storage
        .from_(self.bucket_name)
        .upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )
        )