import os
import time
from slack_sdk import WebClient


from utils.slack_channel_tracker import load_tracker, get_last_ts, update_last_ts

from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

client = WebClient(token=SLACK_BOT_TOKEN)

def fetch_all_messages(channel_id, oldest_ts):
    all_messages = []
    cursor = None
    count = 0
    max_ts_seen = float(oldest_ts)

    while True:
        try:
            response = client.conversations_history(
                channel=channel_id,
                cursor=cursor,
                limit=20,
                oldest=oldest_ts
            )
            messages = response['messages']
            count += len(messages)

            for msg in messages:
                ts = float(msg.get("ts", "0"))
                max_ts_seen = max(max_ts_seen, ts)

                all_messages.append({
                    "ts": msg.get("ts"),
                    "text": msg.get("text", ""),
                    "is_thread_parent": True
                })

                # 🚨 Check for threaded replies
                if msg.get("reply_count", 0) > 0 and "thread_ts" in msg:
                    thread_ts = msg["ts"]
                    try:
                        thread_res = client.conversations_replies(
                            channel=channel_id,
                            ts=thread_ts,
                            limit=100  # Fetch up to 100 replies per thread
                        )
                        replies = thread_res["messages"][1:]  # [0] is the parent message
                        for reply in replies:
                            all_messages.append({
                                "ts": reply.get("ts"),
                                "text": reply.get("text", ""),
                                "is_thread_reply": True,
                                "parent_ts": thread_ts
                            })
                    except SlackApiError as e:
                        print(f"Error fetching thread replies: {e}")

            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break

        except SlackApiError as e:
            print(f"Error fetching messages: {e}")
            break

        print(f"✅ Updated {count} messages so far.")
        time.sleep(30)  # avoid rate-limiting

    return sorted(all_messages, key=lambda x: float(x["ts"])), str(max_ts_seen)


import json

def save_messages_to_json(new_messages, filename="reversed_slack_messages.json"):
    # Load existing messages
    existing_messages = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing_messages = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Existing file is empty or corrupted, starting fresh.")

    # Append new messages (no deduplication or sorting)
    existing_messages.extend(new_messages)

    # Save back to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_messages, f, indent=2, ensure_ascii=False)
    print(f"💾 Appended {len(new_messages)} messages to {filename} (Total: {len(existing_messages)})")

# Run it
# messages = fetch_all_messages(CHANNEL_ID)
# save_messages_to_json(messages)

# Sync one Slack channel
def sync_channel(channel_name, channel_id):
    tracker = load_tracker()
    
    last_ts = get_last_ts(channel_id, tracker)
    print(f"Syncing {channel_name} from ts > {last_ts}")
    reversed_messages, max_ts_seen = fetch_all_messages(channel_id, oldest_ts=last_ts)
    save_messages_to_json(reversed_messages)
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
