# utils/storage_manager.py

from google.cloud import storage
from google.oauth2 import service_account
import os, json

class GCSStorageManager:
    def __init__(self, bucket_name, credentials_path=None):
        if credentials_path:
            creds = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = storage.Client(credentials=creds)
        else:
            self.client = storage.Client()  # fallback to Application Default Credentials
        self.bucket = self.client.bucket(bucket_name)

    def download_file(self, remote_path, local_path):
        blob = self.bucket.blob(remote_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)

    def upload_file(self, local_path, remote_path):
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)

    def load_json(self, remote_path):
        temp_path = f"/tmp/{os.path.basename(remote_path)}"
        self.download_file(remote_path, temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, data, remote_path):
        temp_path = f"/tmp/{os.path.basename(remote_path)}"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.upload_file(temp_path, remote_path)

    def load_text(self, remote_path):
        return self.bucket.blob(remote_path).download_as_text()

