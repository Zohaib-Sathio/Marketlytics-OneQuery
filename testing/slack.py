from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os


client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# def get_channel_id(channel_name):
#     try:
#         response = client.conversations_list(types="public_channel,private_channel", limit=1000,)
#         channels = response['channels']
#         print(len(channels))
#         for channel in channels:
#             # print(channel['name'])
#             if channel['name'] == channel_name:
#                 return channel['id']
#         print(f"Channel '{channel_name}' not found.")
#     except SlackApiError as e:
#         print(f"Error retrieving channels: {e.response['error']}")

def get_channel_messages(channel_id, limit=10):
    try:
        response = client.conversations_history(channel=channel_id, limit=limit)
        messages = response['messages']
        return messages
    except SlackApiError as e:
        print(f"Error retrieving messages: {e.response['error']}")

def extract_text_from_messages(messages):
    # text_messages = []
    for msg in messages:
        print(msg)
        text = msg.get("text", "").strip()
        print(text)
        print("*"*15)
    #     if text:  # only keep messages that have non-empty text
    #         text_messages.append(text)
    # return text_messages

if __name__ == "__main__":
    channel_name = "internal-michigan-autolaw" 
    # channel_id = get_channel_id(channel_name)
    # print(channel_id)
    if True:
        messages = get_channel_messages('C075N244HS7')
        extract_text_from_messages(messages)
