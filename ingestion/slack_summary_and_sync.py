import os
import time
from slack_sdk import WebClient

from utils.gemini_llm import get_gemini_llm
from vector_dbs.slack_db import upsert_summary

from dotenv import load_dotenv

from utils.slack_channel_tracker import load_tracker, get_last_ts, update_last_ts

from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Environment setup
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Clients
client = WebClient(token=SLACK_BOT_TOKEN)
llm = get_gemini_llm()

# Utility: Summarize Slack messages using Gemini
def summarize_text(text: str) -> str:
    prompt = PromptTemplate.from_template(
        """Summarize the following internal Slack conversation for a project knowledge base.
Only include important updates, decisions, progress and action items. Ignore small talk, emojis, or pings. 
Also after all that write a paragraph summary containing information from these messages.

Slack Messages:
{text}

Summary:"""
    )
    chain = prompt | llm
    response = chain.invoke({"text": text})
    return response.content.strip()

# Slack message fetching and summarization logic
def fetch_channel_messages(channel_name, channel_id, oldest_ts):
    count = 0
    cursor = None
    max_ts_seen = oldest_ts

    while True:
        response = client.conversations_history(
            channel=channel_id,
            oldest=oldest_ts,
            limit=200,
            cursor=cursor
        )

        page_msgs = response["messages"]
        if not page_msgs:
            break

        # Filter + summarize
        filtered_texts = [
            msg["text"]
            for msg in page_msgs
        ]
        print(filtered_texts)

        if filtered_texts:
            summary = summarize_text("\n".join(filtered_texts))
            # print(summary)
            # print("*"*25)
            metadata = {
                "source" : "Slack",
                "channel_id": channel_id,
                "channel_name": channel_name,
                "project": channel_name,
            }
            upsert_summary(summary, metadata)

        count += len(page_msgs)
        print(f"✅ Updated {count} messages.")
        max_ts_seen = max(msg["ts"] for msg in page_msgs)
        cursor = response.get("response_metadata", {}).get("next_cursor")

        time.sleep(66)
        if not cursor:
            break

    return count, max_ts_seen

# Sync one Slack channel
def sync_channel(channel_name, channel_id):
    tracker = load_tracker()
    last_ts = get_last_ts(channel_id, tracker)

    print(f"Syncing {channel_name} from ts > {last_ts}")
    count, max_ts_seen = fetch_channel_messages(channel_name, channel_id, oldest_ts=last_ts)
    print(f"✅ Updated {count} messages.")
    update_last_ts(channel_id, max_ts_seen, tracker)
    print(f"✅ Updated tracker for {channel_name} to {max_ts_seen}")


def sync_all_channels():
    tracker = load_tracker()
    for channel_id, meta in tracker.items():
        print(meta['name'])
        sync_channel(channel_name=meta["name"], channel_id=channel_id)

if __name__ == "__main__":
    print("🚀 Starting Slack channel sync...")
    sync_all_channels()
    print("✅ Sync complete.")
