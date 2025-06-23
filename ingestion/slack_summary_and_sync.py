import os
import time
from uuid import uuid4
from slack_sdk import WebClient
from dotenv import load_dotenv

from channel_tracker_utils import load_tracker, get_last_ts, update_last_ts

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma

from langchain.schema import Document

# Load environment variables
load_dotenv()

# Environment setup
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMA_DIR = "vector_store/slack_vector_db"

# Clients
client = WebClient(token=SLACK_BOT_TOKEN)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# Initialize or load Chroma DB
if not os.path.exists(CHROMA_DIR):
    os.makedirs(CHROMA_DIR)

chroma_db = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embedding
)

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

# Utility: Store summary into vector DB
def upsert_summary(summary_text, metadata):
    doc = Document(page_content=summary_text, metadata=metadata)
    chroma_db.add_documents([doc])

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

        if filtered_texts:
            summary = summarize_text("\n".join(filtered_texts))
            # print(summary)
            # print("*"*25)
            metadata = {
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
    last_ts = get_last_ts(channel_name, tracker)

    print(f"Syncing {channel_name} from ts > {last_ts}")
    count, max_ts_seen = fetch_channel_messages(channel_name, channel_id, oldest_ts=last_ts)
    print(f"✅ Updated {count} messages.")
    update_last_ts(channel_id, max_ts_seen, tracker)
    print(f"✅ Updated tracker for {channel_name} to {max_ts_seen}")


def sync_all_channels():
    tracker = load_tracker()
    for channel_id, meta in tracker.items():
        sync_channel(channel_name=meta["name"], channel_id=channel_id)

if __name__ == "__main__":
    print("🚀 Starting Slack channel sync...")
    sync_all_channels()
    print("✅ Sync complete.")
