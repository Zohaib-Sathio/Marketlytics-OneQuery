# ingestion/slack_ingestor.py

import requests
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from your_vector_store import insert_to_vector_db

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_HEADERS = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

def get_project_channels():
    # Map your Slack channels to projects
    return {
        "project-neo": "C01XXXXXXX1",
        "project-nexus": "C02XXXXXXX2",
    }

def fetch_messages(channel_id, latest_ts=None):
    url = f"https://slack.com/api/conversations.history?channel={channel_id}"
    if latest_ts:
        url += f"&oldest={latest_ts}"

    response = requests.get(url, headers=SLACK_HEADERS)
    data = response.json()
    return data.get("messages", [])

def chunk_and_store(text, metadata):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    docs = [{"content": c, "metadata": metadata} for c in chunks]
    insert_to_vector_db(docs)

def process_slack():
    project_channels = get_project_channels()

    for project, channel_id in project_channels.items():
        messages = fetch_messages(channel_id)
        for msg in messages:
            if 'subtype' in msg: continue  # Skip joins, file shares etc.
            text = msg.get("text", "")
            if not text.strip(): continue

            metadata = {
                "source": "slack",
                "project": project,
                "timestamp": msg["ts"],
                "user": msg.get("user", "unknown"),
                "channel": channel_id,
            }
            chunk_and_store(text, metadata)
