import os
import json

from utils.gemini_llm import get_gemini_llm

BASE_PROMPT = """
You are a senior project analyst reviewing a Slack conversation thread to extract accurate and detailed progress over time.

Your job is to:
1. Identify and summarize each meaningful project update or decision.
2. Capture deadlines, milestones, blockers, and next steps.
3. Update or correct previously mentioned info if the newer message provides clarification.
4. Structure the report in chronological order, building one section at a time.
5. Do NOT repeat earlier points unless they were modified or clarified.
6. Remove the unnecessary points.
7. Keep updating the previous report with new updates.
8. If something was not ready or not working and now it is working, then remove the not working part and just add the confirmation of its working.
9. Do not include userids, usernames or links to the report.

Use bullet points, structure by date or topic, and keep it formal, clear, and neutral in tone. This is meant to be read by stakeholders and decision-makers.
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

def build_prompt(previous_report: str, chunk: list):
    message_block = "\n".join(
        f"{m['ts']} - {m['text']}" for m in chunk
    )
    return f"""{BASE_PROMPT}

Here is the existing project summary (if any):
{previous_report}

Now, continue the report using the new Slack messages:
{message_block}

Return ONLY the updated project report so far. Do not include timestamps in the report. No extra response.
"""

def generate_updated_report(previous_report: str, new_messages: list) -> str:
    report = previous_report
    for chunk in chunk_messages(new_messages):
        prompt = build_prompt(report, chunk)
        result = llm.invoke(prompt)
        report = result.content
    return report

def process_channel(channel_name, messages, tracker):
    report_path = os.path.join(REPORT_FOLDER, f"{channel_name}.txt")
    previous_report = ""
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
