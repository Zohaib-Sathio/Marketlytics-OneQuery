import os
from google.cloud import storage

# === Step 1: Set the path to your service account key JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config\gcs_account_key.json"

# === Step 2: Initialize GCS client
client = storage.Client()

bucket_name = "marketlytics-onequery"


# === Step 3: Choose a test bucket and file
bucket_name = "your-bucket-name"  # Replace with your actual bucket name
local_test_file = "test_upload.txt"
remote_blob_name = "test_folder/test_upload.txt"

# === Step 4: Create a dummy file to upload
with open(local_test_file, "w") as f:
    f.write("GCS connection test!")

# === Step 5: Upload file
bucket = client.bucket(bucket_name)
blob = bucket.blob(remote_blob_name)
blob.upload_from_filename(local_test_file)
print(f"✅ Uploaded {local_test_file} to gs://{bucket_name}/{remote_blob_name}")

# === Step 6: Download it back to verify
download_path = "downloaded_test.txt"
blob.download_to_filename(download_path)
print(f"✅ Downloaded blob to {download_path}")
