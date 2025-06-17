from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path

# Scopes define what you want to access – read, write, metadata, etc.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

# SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def list_drive_files():
    # creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10,
        fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(f"{item['name']} ({item['id']})")

if __name__ == '__main__':
    service = authenticate_drive()
    list_drive_files(service)
