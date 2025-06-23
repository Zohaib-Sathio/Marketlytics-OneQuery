from __future__ import print_function
import os.path
import base64
import re
from email import message_from_bytes
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dotenv import load_dotenv
import os


from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_chroma import Chroma 

from langchain.schema import Document


<<<<<<< HEAD
load_dotenv()


=======

load_dotenv()



>>>>>>> 4c05c94 (emails vector database added)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Make sure it's set in .env.")


embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

CHROMA_DIR = "vector_store/emails"

def chunk_and_store_emails(text, metadata, embeddings):
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
    chunks = splitter.split_text(text)
    documents = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

    if not os.path.exists(CHROMA_DIR):
        db = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_DIR)
    else:
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        db.add_documents(documents)

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)

prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an AI assistant that extracts useful information from raw emails."),
    ("human", 
     "Do not return text in markdown version. Given the following email, extract:\n"
     "- Subject\n- Sender\n- Useful content\n\n"
     "Email:\n{email_body}")
])

def extract_email_insights(email_text):
    chain = prompt | llm
    return chain.invoke({"email_body": email_text})


# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


import json
import os

PROCESSED_IDS_FILE = "config/processed_emails.json"

def load_processed_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as file:
        try:
            return set(json.load(file))
        except json.JSONDecodeError:
            return set()

def save_processed_id(email_id):
    processed_ids = load_processed_ids()
    processed_ids.add(email_id)
    with open(PROCESSED_IDS_FILE, "w") as file:
        json.dump(list(processed_ids), file)



from base64 import urlsafe_b64decode

def process_emails(service, max_results=5):

    processed_ids = load_processed_ids()

    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])

    for msg in messages:
        msg_id =  msg['id']
        if msg_id in processed_ids:
            print(f"⏩ Skipping already processed email ID: {msg_id}")
            continue
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data['payload']
        headers = payload['headers']

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

        email_body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        email_body += urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8')

        print(f"📨 Processing email: {subject} from {sender}")
        response = extract_email_insights(email_body)
        print(response.content)
        print('\n\n')
        save_processed_id(msg_id)
        metadata = {
                    "subject": subject,
                    "sender": sender
                }
        chunk_and_store_emails(response.content, metadata, embeddings)

if __name__ == '__main__':
    service = authenticate_gmail()
<<<<<<< HEAD
    process_emails(service, max_results=15)
=======
    process_emails(service, max_results=2)
>>>>>>> 4c05c94 (emails vector database added)
