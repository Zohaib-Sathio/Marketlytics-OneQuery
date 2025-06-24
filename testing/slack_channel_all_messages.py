import os
import time
from slack_sdk import WebClient

from utils.gemini_llm import get_gemini_llm
from vector_dbs.slack_db import upsert_summary

from dotenv import load_dotenv

from utils.slack_channel_tracker import load_tracker, get_last_ts, update_last_ts

from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

client = WebClient(token=SLACK_BOT_TOKEN)

def fetch_all_messages(channel_id):
    all_messages = []
    cursor = None
    count = 0

    while True:
        try:
            response = client.conversations_history(
                channel=channel_id,
                cursor=cursor,
                limit=10,
                oldest=1750446865.428109
            )
            messages = response['messages']
            
            # Store only text and ts
            count += len(messages)
            for msg in messages:
                all_messages.append({
                    "ts": msg.get("ts"),
                    "text": msg.get("text", "")
                })

            # Safely get next_cursor
            metadata = response.get('response_metadata', {})
            cursor = metadata.get('next_cursor', None)

            if not cursor:
                break

        except SlackApiError as e:
            print(f"Error fetching messages: {e}")
            break
        print(f"✅ Updated {count} messages.")

        time.sleep(30)  # Prevent rate limiting

    # Return in chronological order
    return all_messages, list(sorted(all_messages, key=lambda x: float(x["ts"])))

import json

def save_messages_to_json(messages, filename="tempreversed_slack_messages.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    print(f"{len(messages)} messages saved to {filename}")

def save_messages_(messages, filename="temporiginal_slack_messages.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    print(f"{len(messages)} messages saved to {filename}")

# Run it
# messages = fetch_all_messages(CHANNEL_ID)
# save_messages_to_json(messages)

# Sync one Slack channel
def sync_channel(channel_name, channel_id):
    tracker = load_tracker()
    messages, reversed_messages = fetch_all_messages(channel_id)
    save_messages_(messages)
    save_messages_to_json(reversed_messages)
    # last_ts = get_last_ts(channel_id, tracker)

    # print(f"Syncing {channel_name} from ts > {last_ts}")
    # count, max_ts_seen = fetch_channel_messages(channel_name, channel_id, oldest_ts=last_ts)
    # print(f"✅ Updated {count} messages.")
    # update_last_ts(channel_id, max_ts_seen, tracker)
    # print(f"✅ Updated tracker for {channel_name} to {max_ts_seen}")


def sync_all_channels():
    tracker = load_tracker()
    for channel_id, meta in tracker.items():
        print(meta['name'])
        sync_channel(channel_name=meta["name"], channel_id=channel_id)

if __name__ == "__main__":
    print("🚀 Starting Slack channel sync...")
    sync_all_channels()
    print("✅ Sync complete.")
