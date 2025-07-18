import os
import time
from slack_sdk import WebClient


from utils.slack_channel_tracker import load_tracker, get_last_ts, update_last_ts
from utils.storage_manager import GCSStorageManager

gcs = GCSStorageManager("marketlytics-onequery", "config/gcs_account_key.json")

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
                    print("count: ", {msg.get("reply_count", 0)})
                    thread_ts = msg["ts"]
                    time.sleep(2)
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
        time.sleep(60)  # avoid rate-limiting

    return sorted(all_messages, key=lambda x: float(x["ts"])), str(max_ts_seen)


def save_messages_to_json(new_messages, channel_name, gcs):
    remote_path = f"slack_data/{channel_name}.json"

    existing_messages = []
    try:
        existing_messages = gcs.load_json(remote_path)
    except Exception:
        print(f"⚠️ Couldn't load existing messages for {channel_name}. Starting fresh.")

    existing_messages.extend(new_messages)
    gcs.save_json(existing_messages, remote_path)

    print(f"💾 Saved {len(new_messages)} messages to {remote_path} (Total: {len(existing_messages)})")




def sync_channel(channel_id, channel_meta):
    
    tracker = load_tracker()

    last_ts = get_last_ts(channel_id, tracker)
    channel_name = channel_meta["name"]
    print(f"🔄 Syncing /{channel_name} from ts > {last_ts}")

    messages, max_ts_seen = fetch_all_messages(channel_id, oldest_ts=last_ts)

    save_messages_to_json(messages, channel_name, gcs)
    update_last_ts(channel_id, max_ts_seen, tracker)
    print(f"✅ Updated tracker for {channel_name} to {max_ts_seen}")



def sync_all_channels():
    tracker = load_tracker()
    for channel_id, meta in tracker.items():
        sync_channel(channel_id, meta)
        time.sleep(60)

if __name__ == "__main__":
    print("🚀 Starting Slack channel sync...")
    sync_all_channels()
    print("✅ Sync complete.")
