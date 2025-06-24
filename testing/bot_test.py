from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))


def fetch_all_bot_channels():
    all_channels = []
    cursor = None

    while True:
        response = client.conversations_list(
            types="public_channel,private_channel",
            limit=1000,
            cursor=cursor
        )
        all_channels.extend(response["channels"])
        cursor = response["response_metadata"].get("next_cursor")
        if not cursor:
            break

    return [c["name"] for c in all_channels]


def is_bot_member_of_channel(channel_name):
    channels = fetch_all_bot_channels()
    return channel_name in channels


