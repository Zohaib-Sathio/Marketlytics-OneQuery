# utils/storage_manager.py

from google.cloud import storage
from google.oauth2 import service_account
import os, json

class GCSStorageManager:
    def __init__(self, bucket_name, credentials_path=None, credentials_dict=None):
        if credentials_dict:
            creds = service_account.Credentials.from_service_account_info(credentials_dict)
            self.client = storage.Client(credentials=creds)
        elif credentials_path:
            creds = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = storage.Client(credentials=creds)
        else:
            self.client = storage.Client()  # fallback to ADC (won’t work on Streamlit Cloud)

        self.bucket = self.client.bucket(bucket_name)

    def download_file(self, remote_path, local_path):
        blob = self.bucket.blob(remote_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
    
    def download_text_file(self, remote_path: str, local_path: str):
        blob = self.bucket.blob(remote_path)
        blob.download_to_filename(local_path)
        print(f"✅ Downloaded {remote_path} → {local_path}")


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
    
    def upload_json(self, data: dict, remote_path: str):
        blob = self.bucket.blob(remote_path)
        blob.upload_from_string(json.dumps(data), content_type="application/json")


