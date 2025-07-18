from utils.storage_manager import GCSStorageManager

gcs = GCSStorageManager("marketlytics-onequery", "config/gcs_account_key.json")

files = [
    "slack_project_reports/internal-geotrek.txt",
    "slack_project_reports/internal-michigan-autolaw.txt",
    "slack_project_reports/internal_innerview.txt",
    "slack_project_reports/internal_trupanion.txt"
]

for remote_path in files:
    local_path = remote_path.split("/")[-1]  # Save as: internal-geotrek.txt, etc.
    gcs.download_text_file(remote_path, local_path)
