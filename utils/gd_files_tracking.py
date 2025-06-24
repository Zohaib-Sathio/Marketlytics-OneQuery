import os
import json

PROCESSED_IDS_FILE = "config/processed_gd_files.json"

def load_gd_processed_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as file:
        try:
            return set(json.load(file))
        except json.JSONDecodeError:
            return set()

def save_gd_processed_id(file_id):
    processed_ids = load_gd_processed_ids()
    processed_ids.add(file_id)
    with open(PROCESSED_IDS_FILE, "w") as file:
        json.dump(list(processed_ids), file)
