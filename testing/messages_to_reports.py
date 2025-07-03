import os
import json

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

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def chunk_messages(messages, chunk_size=20):
    for i in range(0, len(messages), chunk_size):
        yield messages[i:i + chunk_size]

from datetime import datetime

def format_ts(ts):
    """Convert Slack ts to readable datetime string."""
    return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")

def build_prompt(previous_report: str, chunk: list):
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
- Do NOT add commentary or explanations. Just return the updated project report.
"""

import time

def generate_updated_report(previous_report: str, new_messages: list) -> str:
    report = previous_report
    messages_count = 0
    for chunk in chunk_messages(new_messages):
        prompt = build_prompt(report, chunk)
        result = llm.invoke(prompt)
        report = result.content
        messages_count += 20
        print(f'{messages_count} processed.')
        time.sleep(10)
    return report

def process_channel(channel_name, messages, tracker):
    report_path = os.path.join(REPORT_FOLDER, f"{channel_name}.txt")
    previous_report = f"This is the project progress report for {channel_name}: "
    last_ts = 0.0

    if channel_name in tracker:
        last_ts = float(tracker[channel_name]["last_ts"])
        report_path = tracker[channel_name]["report_path"]
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                previous_report = f.read()

    # Filter new messages
    new_messages = [m for m in messages if float(m["ts"]) > last_ts]

    if not new_messages:
        print(f"🟡 No new messages to update for {channel_name}")
        return

    new_last_ts = max(float(m["ts"]) for m in new_messages)
    updated_report = generate_updated_report(previous_report, new_messages)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(updated_report)

    tracker[channel_name] = {
        "report_path": report_path,
        "last_ts": str(new_last_ts)
    }

    print(f"✅ Updated report for {channel_name}, saved to {report_path}")


def run_all():
    tracker = load_json(TRACKER_PATH)

    for filename in os.listdir(DATA_FOLDER):
        if not filename.endswith(".json"):
            continue

        channel_name = filename.replace(".json", "")
        filepath = os.path.join(DATA_FOLDER, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ Failed to parse messages from {filename}")
                continue

        process_channel(channel_name, messages, tracker)

    save_json(tracker, TRACKER_PATH)
    print("🚀 All reports updated.")


if __name__ == "__main__":
    run_all()
