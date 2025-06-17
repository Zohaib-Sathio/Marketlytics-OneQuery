# ingestion/google_drive_ingestor.py

# # from googleapiclient.discovery import build
# from google.oauth2 import service_account
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from your_vector_store import insert_to_vector_db  # You'll implement this
import fitz  # PyMuPDF


import json
import os

from docx import Document

import io
from googleapiclient.http import MediaIoBaseDownload
# from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

# SETUP
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'config/credentials.json'

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

def authenticate_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('config/credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def list_files(service, mime_type_filter=None):
    print("listing files")
    query = f"mimeType='{mime_type_filter}'" if mime_type_filter else ""
    results = service.files().list(q=query, pageSize=10, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])


def download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()


def extract_text_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def extract_text_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_txt(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def extracted_text(f, service):
    # print(f['id'], "  ", f['name'])
    
    print(f"Processing: {f['name']}")
    download_file(service, f['id'], f['name'])
    # print("file downloaded")
    if f['name'].endswith('.pdf'):
        return extract_text_pdf(f['name'])
    elif f['name'].endswith('.docx'):
        return extract_text_docx(f['name'])
    elif f['name'].endswith('.txt'):
        return extract_text_txt(f['name'])



PROCESSED_IDS_FILE = "config/processed_gd_files.json"

def load_gd_processed_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as file:
        try:
            return set(json.load(file))
        except json.JSONDecodeError:
            return set()

def save_gd_processed_id(file_id):
    processed_ids = load_gd_processed_ids()
    processed_ids.add(file_id)
    with open(PROCESSED_IDS_FILE, "w") as file:
        json.dump(list(processed_ids), file)


from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(text)
from langchain.schema import Document


def create_documents(chunks, metadata):
    return [Document(page_content=chunk, metadata=metadata) for chunk in chunks]


from langchain.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma 

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os

# Optional: Switch to HuggingFace for local
from langchain.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

CHROMA_DIR = "vector_store/chroma"
# EMBEDDINGS = OpenAIEmbeddings()  # You can swap this later

def chunk_and_store(text, metadata, embeddings):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    documents = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

    if not os.path.exists(CHROMA_DIR):
        db = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_DIR)
    else:
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        db.add_documents(documents)
    db.persist()



def process_drive():
    service = authenticate_drive()
    files = list_files(service)
    processed_ids = load_gd_processed_ids()
    for file in files:
        file_id =  file['id']
        file_name = file['name']
        if file_id in processed_ids:
            print(f"⏩ Skipping already processed file : {file_name} {file_id}")
            continue

        if file['name'].endswith('.pdf') or file['name'].endswith('.docx') or file['name'].endswith('.txt'):
            try:
                text = extracted_text(file, service)
                if not text.strip(): continue
                metadata = {
                    "source": "google_drive",
                    "file_name": file["name"],
                    "project": "testing",
                    "file_id": file["id"]
                }
                # print(text, "  ", metadata)
                save_gd_processed_id(file_id)
                chunk_and_store(text, metadat, embeddings)
            except Exception as e:
                print(f"[!] Failed on {file['name']}: {e}")


from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Make sure it's set in .env.")

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)




if __name__ == "__main__":
    # process_drive()
    
    from langchain.chains import RetrievalQA
    db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # simplest, can be replaced with map_reduce or refine
        retriever=db.as_retriever(search_kwargs={"k": 3})
    )
    query = "What projects am I working on right now?"
    response = qa_chain.invoke({"query": query})
    print(response)


    # from langchain.vectorstores import Chroma

    # db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    # results = db.similarity_search("what projects am i working on right now?", k=2)

    # for doc in results:
    #     print('DOC: ')
    #     print(doc.page_content)
    #     print(doc.metadata)

