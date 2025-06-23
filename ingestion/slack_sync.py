import os
from slack_sdk import WebClient
from channel_tracker_utils import load_tracker, save_tracker, get_last_ts, update_last_ts
# from vector_store import upsert_document, document_exists
from dotenv import load_dotenv
load_dotenv()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

import time 

def fetch_channel_messages(channel_id, oldest_ts):
    messages = []
    cursor = None
    while True:
        response = client.conversations_history(
            channel=channel_id,
            oldest=oldest_ts,
            limit=50,
            cursor=cursor
        )
        messages.extend(response["messages"])
        for msg in messages:
            text = msg.get("text", "")
            print(text)
            print('*'*20)
        cursor = response.get("response_metadata", {}).get("next_cursor")
        time.sleep(65)
        if not cursor:
            break
    return messages

def sync_channel(channel_name, channel_id):
    tracker = load_tracker()
    last_ts = get_last_ts(channel_name, tracker)
    
    print(f"Syncing {channel_name} from ts > {last_ts}")
    messages = fetch_channel_messages(channel_id, oldest_ts=last_ts)
    print(f"Fetched {len(messages)} messages.")

    max_ts_seen = last_ts
    for msg in messages:
        msg_id = msg["ts"]
        text = msg.get("text", "")
        print(text)
        # edited_ts = msg.get("edited", {}).get("ts", None)

        # if document_exists(msg_id) and not edited_ts:
        #     continue

        # metadata = {
        #     "channel": channel_name,
        #     "author": msg.get("user", "unknown"),
        #     "timestamp": msg["ts"]
        # }

        # upsert_document(msg_id, text, metadata)
        # max_ts_seen = max(max_ts_seen, msg["ts"])

    update_last_ts(channel_name, max_ts_seen, tracker)
    print(f"Updated tracker for {channel_name} to {max_ts_seen}")



if __name__ == "__main__":
    from slack_sync import sync_channel
    tracker = load_tracker()

    for channel_id, meta in tracker.items():
        sync_channel(channel_name=meta["name"], channel_id=channel_id)
