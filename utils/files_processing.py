import fitz  # PyMuPDF

import io

from docx import Document as DocxDocument # to avoid conflict with document import from langchain

from googleapiclient.http import MediaIoBaseDownload

def extract_text_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def extract_text_docx(file_path):
    doc = DocxDocument(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_txt(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
def download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()


def extracted_text(f, service):
    print(f"Processing: {f['name']}")
    download_file(service, f['id'], f['name'])
    file_path = f['name']

    if file_path.endswith('.pdf'):
        text = extract_text_pdf(file_path)
    elif file_path.endswith('.docx'):
        text = extract_text_docx(file_path)
    elif file_path.endswith('.txt'):
        text = extract_text_txt(file_path)
    else:
        text = None

    return text, file_path
