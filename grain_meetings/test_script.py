import os
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment setup
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Clients
client = WebClient(token=SLACK_BOT_TOKEN)
CHANNEL_ID = "C0920498CP8"




def get_full_grain_summary_text(slack_message):
    blocks = slack_message.get("blocks", [])
    if not blocks or len(blocks) < 3:
        return ""


    full_text = ""
    for block in blocks:
        text_block = block.get("text", {}).get("text", "")
        full_text += text_block + "\n\n"
    
    return full_text.strip()


from langchain_core.prompts import ChatPromptTemplate
from utils.gemini_llm import get_gemini_llm

llm = get_gemini_llm()

grain_summary_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a structured summarizer for Grain meeting summaries shared on Slack. "
     "Your job is to take raw, messy meeting summary text — which may include emojis, Slack markdown, timestamps, and links — and return a clean, context-rich, self-contained summary suitable for storage in a vector database used in RAG systems."),
    
    ("human",
     "Clean the following meeting summary by:\n"
     "- Removing all special characters, links, and timestamps (like `t=123456`, `:arrow_forward:`, `<!date^...>`)\n"
     "- Normalizing formatting: replace bullet symbols (•, ☐) with plain text bullets (e.g., '-')\n"
     "- Preserve section headings like 'Key Takeaways', 'Discussion Topics', and 'Action Items'\n"
     "- Ensure the result is human-readable and can be used in semantic search\n"
     "- Do not use markdown — return the cleaned summary as plain text\n\n"
     "Meeting Summary:\n{raw_summary}")
])

def extract_clean_meeting_summary(raw_summary_text):
    chain = grain_summary_prompt | llm
    return chain.invoke({"raw_summary": raw_summary_text})


def fetch_messages(channel_id, limit=1000):
    messages = []
    next_cursor = None

    while True:
        try:
            response = client.conversations_history(
                channel=channel_id,
                limit=200,
                cursor=next_cursor
            )

            for msg in response.get("messages", []):
                # print(msg)
                # Example usage
                raw_meeting_text = get_full_grain_summary_text(msg)  # from earlier step
                if raw_meeting_text:
                    cleaned_summary = extract_clean_meeting_summary(raw_meeting_text)
                    print(cleaned_summary.content)

            next_cursor = response.get("response_metadata", {}).get("next_cursor")
            if not next_cursor:
                break
            time.sleep(10)

        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
            break

    return messages


if __name__ == "__main__":
    msgs = fetch_messages(CHANNEL_ID)