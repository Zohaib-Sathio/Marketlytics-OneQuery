import json
import os

TRACKER_FILE = "config/channel_tracker.json"

def load_tracker():
    if not os.path.exists(TRACKER_FILE):
        return {}
    with open(TRACKER_FILE, "r") as f:
        return json.load(f)

def save_tracker(tracker):
    with open(TRACKER_FILE, "w") as f:
        json.dump(tracker, f, indent=4)

def get_last_ts(channel_id, tracker):
    # Return 0 if not found
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
