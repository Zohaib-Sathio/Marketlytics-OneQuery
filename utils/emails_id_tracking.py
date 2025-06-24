import os
import json

PROCESSED_IDS_FILE = "config/processed_emails.json"

def load_processed_email_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as file:
        try:
            return set(json.load(file))
        except json.JSONDecodeError:
            return set()

def save_processed_email_id(email_id):
    processed_ids = load_processed_email_ids()
    processed_ids.add(email_id)
    with open(PROCESSED_IDS_FILE, "w") as file:
        json.dump(list(processed_ids), file)
