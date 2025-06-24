from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.gemini_llm import get_gemini_llm

import os


# Setup Gemini model
llm = get_gemini_llm()

# Slack client setup
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# Step 1: Get all channel names
def get_all_channel_names():
    try:
        response = client.conversations_list()
        return [channel['name'] for channel in response['channels']]
    except SlackApiError as e:
        print(f"Error retrieving channels: {e.response['error']}")
        return []

def get_all_channels_with_descriptions():
    try:
        response = client.conversations_list()
        channels_info = []
        for channel in response['channels']:
            name = channel['name']
            description = channel.get('purpose', {}).get('value', 'No description provided')
            channels_info.append({'name': name, 'description': description})
        return channels_info
    except SlackApiError as e:
        print(f"Error retrieving channels: {e.response['error']}")
        return []
def decide_best_channel_with_description(user_query, channels_info):
    formatted_channels = "\n".join(
        [f"- {channel['name']}: {channel['description']}" for channel in channels_info]
    )
    prompt = f"""
You are an intelligent assistant tasked with selecting the best Slack channel for a user's query.

User query:
\"\"\"{user_query}\"\"\"

Here are the available channels and their descriptions:
{formatted_channels}

Instructions:
- Return only the channel **name** that is most relevant to the query.
- If you're not 100% sure, return: unknown
- No explanation. Just the exact channel name.

Your answer:
"""
    result = llm.invoke(prompt)
    return result.content.strip().lower()


# Step 2: Gemini decides the best-matching channel
def decide_best_channel(user_query, channel_names):
    prompt = f"""
You're given a user query and a list of Slack channel names.

User query:
\"\"\"{user_query}\"\"\"

Available channels:
{', '.join(channel_names)}

Your task:
- Return only the **most relevant** channel name from the list.
- If you're **not 100% sure**, return the string: unknown.
ONLY return the name. No explanation.
"""
    result = llm.invoke(prompt)
    return result.content.strip().lower()

# Step 3: Fetch channel ID
def get_channel_id(channel_name):
    try:
        response = client.conversations_list()
        for channel in response['channels']:
            if channel['name'].lower() == channel_name.lower():
                return channel['id']
        print(f"Channel '{channel_name}' not found.")
    except SlackApiError as e:
        print(f"Error retrieving channels: {e.response['error']}")

# Step 4: Fetch messages
def get_channel_messages(channel_id, limit=10):
    try:
        response = client.conversations_history(channel=channel_id, limit=limit)
        return response['messages']
    except SlackApiError as e:
        print(f"Error retrieving messages: {e.response['error']}")

# Step 5: Print messages
def extract_text_from_messages(messages):
    for msg in messages:
        text = msg.get("text", "").strip()
        if text:
            print(text)
            print("*" * 15)

# MAIN DRIVER
if __name__ == "__main__":
    while True:
        user_query = input("Enter your query: ")

        if user_query == "q":
            break

        all_channels = get_all_channels_with_descriptions()
        best_channel = decide_best_channel_with_description(user_query, all_channels)

        if best_channel == "unknown":
            print("❌ Gemini could not confidently select a channel for this query.")
        else:
            print(f"✅ Gemini chose channel: #{best_channel}")
            # channel_id = get_channel_id(best_channel)
            # if channel_id:
            #     messages = get_channel_messages(channel_id)
            #     extract_text_from_messages(messages)
