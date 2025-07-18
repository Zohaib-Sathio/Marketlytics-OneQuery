# utils/upload_existing_files.py

import os
from utils.storage_manager import GCSStorageManager

BUCKET = "marketlytics-onequery"
gcs = GCSStorageManager(bucket_name=BUCKET, credentials_path = "config/gcs_account_key.json")

def upload_folder(local_folder, remote_prefix):
    for root, dirs, files in os.walk(local_folder):
        for file in files:
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, local_folder)
            remote_path = f"{remote_prefix}/{rel_path}".replace("\\", "/")
            gcs.upload_file(local_path, remote_path)
            print(f"✅ Uploaded: {remote_path}")

# upload_folder("slack_data", "slack_data")
# upload_folder("slack_project_reports", "slack_project_reports")
# gcs.upload_file("slack_project_reports/report_tracker.json", "slack_project_reports/report_tracker.json")
# gcs.upload_file("config/channel_tracker.json", "slack_channel_tracker.json")
gcs.upload_file(
    local_path="config/tracker_to_clickup_map.json",
    remote_path="config/tracker_to_clickup_map.json"
)
