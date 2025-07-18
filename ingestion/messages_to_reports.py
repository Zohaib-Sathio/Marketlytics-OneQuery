import os
from utils.gemini_llm import get_gemini_llm

BASE_PROMPT = """
You are a senior project analyst reviewing a Slack conversation thread to generate a living project report. Your job is to continuously refine and update the report to reflect the most accurate and current state of the project.

Instructions:

1. Identify and summarize **each meaningful update**, decision, blocker, milestone, or deadline from the conversation.
2. Structure the report **by date**, ensuring that each update is tagged with the date of the message for traceability.
3. If a **previously mentioned item is resolved or contradicted**, modify or remove it accordingly. The report must reflect the **latest truth**, not historical confusion.
4. If a message confirms that something previously marked as pending or broken is now resolved, **remove the old status** and **only keep the updated confirmation**.
5. Do **not repeat** previously captured information unless it has been changed or clarified.
6. Recognize and include **names of clients, external stakeholders, or organizations** mentioned in the messages even if they are not Slack users.
7. Only include meaningful information — omit off-topic, casual, or redundant messages.
8. Ensure the final report reads like a **chronological project brief** with dated bullet points, clear subtopics, and professional tone.
9. Do not include user IDs.

Your output will be used by LLMs for reasoning, so clarity, chronological structure, and factual updates are essential.
"""


DATA_FOLDER = "slack_data"
REPORT_FOLDER = "slack_project_reports"
TRACKER_PATH = "slack_project_reports/report_tracker.json"

os.makedirs(REPORT_FOLDER, exist_ok=True)
llm = get_gemini_llm()

from utils.storage_manager import GCSStorageManager

gcs = GCSStorageManager("marketlytics-onequery", "config/gcs_account_key.json")

def load_json(remote_path):
    try:
        return gcs.load_json(remote_path)
    except Exception:
        return {}

def save_json(data, remote_path):
    gcs.save_json(data, remote_path)

def chunk_messages(messages, chunk_size=20):
    for i in range(0, len(messages), chunk_size):
        yield messages[i:i + chunk_size]

from datetime import datetime

def format_ts(ts):
    """Convert Slack ts to readable datetime string."""
    return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")

def build_prompt(previous_report: str, chunk: list):
    # print(f"{format_ts(m['ts'])} - {m['text']}" for m in chunk)
    message_block = "\n".join(
        f"{format_ts(m['ts'])} - {m['text']}" for m in chunk
    )
    return f"""{BASE_PROMPT}

Here is the existing project summary (if any):
{previous_report}

Now, continue the report using the new Slack messages:
{message_block}

Your job is to:
- Integrate all relevant new updates into the correct date-based sections.
- Ensure the report reflects only the most accurate and current state.
- Preserve chronological order by date.
- Do NOT repeat old content unless it was changed.
- Include date headings, but NOT exact timestamps.
- Do NOT add commentary or explanations. Just return the updated section by date that I can append to previous report.
- Do NOT respond back with whole report, just RETURN the updated report section that can be append to the report, nothing extra.
- If you see any update is added to the report already on that same data then you can ignore that update and only RETURN other updates of that day if given in messages.
"""

import time

def generate_updated_report(previous_report: str, new_messages: list) -> str:
    report = previous_report
    messages_count = 0
    for chunk in chunk_messages(new_messages, 25):
        prompt = build_prompt(report, chunk)
        result = llm.invoke(prompt)
        # print(result.content)
        report += f"\n\n {result.content}"
        messages_count += len(chunk)
        print(f'{messages_count} processed.')
        time.sleep(10)
    return report


from io import BytesIO

def upload_text_to_gcs(text: str, remote_path: str):
    buffer = BytesIO(text.encode("utf-8"))  # 🔥 Force encoding to bytes
    blob = gcs.bucket.blob(remote_path)
    blob.upload_from_file(buffer, content_type="text/plain")
    print(f"✅ Uploaded {remote_path}")
    

def process_channel(channel_name, messages, tracker):
    report_path = f"slack_project_reports/{channel_name}.txt"
    # remote_tracker_path = "slack_project_reports/report_tracker.json"

    previous_report = f"This is the project progress report for {channel_name}: "
    last_ts = 0.0

    if channel_name in tracker:
        last_ts = float(tracker[channel_name]["last_ts"])
        report_path = tracker[channel_name]["report_path"]
        try:
            previous_report = gcs.load_text(report_path)
        except Exception as e:
            print(f"⚠️ Failed to load previous report for {channel_name}: {e}")

    new_messages = [m for m in messages if float(m["ts"]) > last_ts]
    if not new_messages:
        print(f"🟡 No new messages for {channel_name}")
        return

    new_last_ts = max(float(m["ts"]) for m in new_messages)
    updated_report = generate_updated_report(previous_report, new_messages)

    upload_text_to_gcs(updated_report, report_path)


    tracker[channel_name] = {
        "report_path": report_path,
        "last_ts": str(new_last_ts)
    }

    print(f"✅ Report updated for {channel_name}")
 


def run_all():
    # Load tracker from GCS, not local disk
    tracker = gcs.load_json("slack_project_reports/report_tracker.json")

    for blob in gcs.client.list_blobs(gcs.bucket, prefix="slack_data/"):
        if not blob.name.endswith(".json"):
            continue

        channel_name = os.path.basename(blob.name).replace(".json", "")
        try:
            messages = gcs.load_json(blob.name)
            process_channel(channel_name, messages, tracker)
        except Exception as e:
            print(f"❌ Failed for {channel_name}: {e}")

    # Save tracker back to GCS, not local disk
    try:
        gcs.save_json(tracker, "slack_project_reports/report_tracker.json")
    except Exception as e:
        print(f"❌ Failed to save report tracker: {e}")
    print("🚀 All reports processed.")

from ingestion.slack_channel_all_messages import sync_all_channels

if __name__ == "__main__":
    sync_all_channels()
    run_all()
