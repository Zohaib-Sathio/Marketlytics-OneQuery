# utils/slack_channel_tracker.py

import json
from utils.storage_manager import GCSStorageManager

BUCKET_NAME = "marketlytics-onequery"
TRACKER_FILE = "slack_channel_tracker.json"

gcs = GCSStorageManager(BUCKET_NAME, credentials_path="config/gcs_account_key.json")

def load_tracker():
    try:
        return gcs.load_json(TRACKER_FILE)
    except Exception as e:
        print(f"⚠️ Could not load tracker: {e}")
        return {}

def save_tracker(tracker):
    try:
        gcs.save_json(tracker, TRACKER_FILE)
    except Exception as e:
        print(f"❌ Failed to save tracker: {e}")
        raise e

def get_last_ts(channel_id, tracker):
    return tracker.get(channel_id, {}).get("last_ts", "0")

def update_last_ts(channel_id, new_ts, tracker):
    if channel_id not in tracker:
        raise KeyError(f"Channel ID {channel_id} not found in tracker.")
    tracker[channel_id]["last_ts"] = new_ts
    save_tracker(tracker)

def register_new_project(channel_id, channel_name, project_name):
    tracker = load_tracker()
    if channel_id in tracker:
        print(f"⚠️ Channel {channel_name} already registered.")
        return False

    tracker[channel_id] = {
        "name": channel_name,
        "project": project_name,
        "last_ts": "0"
    }
    save_tracker(tracker)
    print(f"✅ Registered project: {project_name} (channel: {channel_name})")
    return True
