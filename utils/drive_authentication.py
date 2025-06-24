import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
USER_CREDENTIALS_FILE = 'config/credentials.json'
TOKEN_PATH = 'token.json'

def authenticate_drive():
    creds = None

    # 1. Load existing token if available
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # 2. Refresh token if expired and refresh_token is available
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # 3. Do full browser login if no creds or can't refresh
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(USER_CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)
