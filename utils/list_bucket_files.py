# utils/list_bucket_files.py

from google.cloud import storage
from google.oauth2 import service_account

def list_files(bucket_name, credentials_path=None):
    if credentials_path:
        creds = service_account.Credentials.from_service_account_file(credentials_path)
        client = storage.Client(credentials=creds)
    else:
        client = storage.Client()  # will use ADC if available

    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    print(f"📂 Files in bucket '{bucket_name}':")
    for blob in blobs:
        print(f" - {blob.name}")

if __name__ == "__main__":
    list_files(
        bucket_name="marketlytics-onequery",
        credentials_path="config/gcs_account_key.json"
    )
