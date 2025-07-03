import os

import os
import time
from slack_sdk import WebClient


from utils.slack_channel_tracker import load_tracker, get_last_ts, update_last_ts

from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

client = WebClient(token=SLACK_BOT_TOKEN)


import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file']  # ✅ Can upload files your app creates

USER_CREDENTIALS_FILE = 'config/credentials.json'
TOKEN_PATH = 'token.json'

def authenticate_drive():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(USER_CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)




def fetch_all_messages_with_files(channel_id, oldest_ts):
    shared_files = []
    cursor = None

    while True:
        try:
            response = client.conversations_history(
                channel=channel_id,
                cursor=cursor,
                limit=200,
                oldest=oldest_ts
            )
            google_file_links = []
            import re

            messages = response['messages']

            for msg in messages:
                if 'text' in msg:
                    links = re.findall(r'https?://(?:drive|docs)\.google\.com/[^\s>]+', msg['text'])
                    for link in links:
                        if any(x in link for x in ['document', 'spreadsheets']):
                            google_file_links.append(link)
                if 'files' in msg:
                    for f in msg['files']:
                        if f['filetype'] in ['pdf', 'doc', 'docx']:
                            shared_files.append({
                                'name': f['name'],
                                'url': f['url_private'],
                                'filetype': f['filetype']
                            })
                
                # 🚨 Check for threaded replies
                if msg.get("reply_count", 0) > 0 and "thread_ts" in msg:
                    print("count: ", {msg.get("reply_count", 0)})
                    thread_ts = msg["ts"]
                    time.sleep(5)
                    try:
                        thread_res = client.conversations_replies(
                            channel=channel_id,
                            ts=thread_ts,
                            limit=100  # Fetch up to 100 replies per thread
                        )
                        replies = thread_res["messages"][1:]  # [0] is the parent message
                        for reply in replies:
                            if 'text' in reply:
                                links = re.findall(r'https?://(?:drive|docs)\.google\.com/[^\s>]+', msg['text'])
                                for link in links:
                                    if any(x in link for x in ['document', 'spreadsheets']):
                                        google_file_links.append(link)
                            if 'files' in reply:
                                for f in reply['files']:
                                    if f['filetype'] in ['pdf', 'doc', 'docx']:
                                        shared_files.append({
                                            'name': f['name'],
                                            'url': f['url_private'],
                                            'filetype': f['filetype']
                                        })
                    except SlackApiError as e:
                        print(f"Error fetching thread replies: {e}")

            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break

        except SlackApiError as e:
            print(f"Slack error: {e}")
            break

        time.sleep(60)

    all_shared_docs = shared_files + [{"name": "Google Drive Link", "url": link, "filetype": "gdoc/gsheet"} for link in google_file_links]

# Optional: Print nicely
    for doc in all_shared_docs:
        print(f"[{doc['filetype'].upper()}] {doc['name']} → {doc['url']}")

    # print(all_files)
    # return all_files

import requests
import io
from googleapiclient.http import MediaIoBaseUpload

def upload_file_to_drive(file_obj, drive_service):
    if 'url_private_download' not in file_obj:
        print(f"⚠️ Skipping file (no download URL): {file_obj.get('name', '[unknown]')}")
        return

    file_url = file_obj['url_private_download']
    file_name = file_obj['name']
    mimetype = file_obj.get('mimetype', 'application/octet-stream')

    headers = {'Authorization': f'Bearer {SLACK_BOT_TOKEN}'}
    res = requests.get(file_url, headers=headers)

    if res.status_code == 200:
        file_stream = io.BytesIO(res.content)
        media = MediaIoBaseUpload(file_stream, mimetype=mimetype)

        uploaded = drive_service.files().create(
            body={'name': file_name, 'parents': ['1j-jnVqNhAZVjw5apae2UBV2-Is6PtRiW']},  # ⬅️ replace folder ID
            media_body=media,
            fields='id'
        ).execute()

        print(f"✅ Uploaded: {file_name} → Drive ID: {uploaded['id']}")
    else:
        print(f"❌ Failed to download: {file_name} | Status: {res.status_code}")

if __name__ == "__main__":
    channel_id = 'C08RY72251U'  
    drive_service = authenticate_drive()
    oldest_ts = "0"

    slack_files = fetch_all_messages_with_files(channel_id, oldest_ts)

    # for file_obj in slack_files:
    #     upload_file_to_drive(file_obj, drive_service)


