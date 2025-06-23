from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

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


def list_files(service, mime_type_filter=None):
    print("listing files")
    query = f"mimeType='{mime_type_filter}'" if mime_type_filter else ""
    results = service.files().list(q=query, pageSize=10, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])


from googleapiclient.http import MediaIoBaseDownload
import io

def download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
import fitz  # PyMuPDF

def extract_text_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


from docx import Document

def extract_text_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_txt(file_path):
    with open(file_path, 'r') as file:
        return file.read()



service = authenticate_drive()
files = list_files(service)  # or docx, etc.
for f in files:
    print(f['id'], "  ", f['name'])
    if f['name'].endswith('.pdf') or f['name'].endswith('.docx') or f['name'].endswith('.txt'):
        print(f"Processing: {f['name']}")
        download_file(service, f['id'], f['name'])
        print("file downloaded")
        if f['name'].endswith('.pdf'):
            print(extract_text_pdf(f['name']))
        elif f['name'].endswith('.docx'):
            print(extract_text_docx(f['name']))
        elif f['name'].endswith('.txt'):
            print(extract_text_txt(f['name']))

