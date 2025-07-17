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
    
def download_file(service, file_id, file_name, mime_type):
    # If it's a Google Docs format, export it
    export_mime_types = {
        "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/vnd.google-apps.spreadsheet": "text/csv",  # .csv
        "application/vnd.google-apps.presentation": "application/pdf",  # .pdf
    }

    if mime_type in export_mime_types:
        request = service.files().export_media(fileId=file_id, mimeType=export_mime_types[mime_type])
        extension = {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "text/csv": ".csv",
            "application/pdf": ".pdf"
        }[export_mime_types[mime_type]]

        file_name = file_name + extension
    else:
        request = service.files().get_media(fileId=file_id)

    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    return file_name


def extracted_text(f, service):
    print(f"📄 Extracting text from: {f['name']}")

    downloaded_file = download_file(service, f['id'], f['name'], f['mimeType'])

    if downloaded_file.endswith('.pdf'):
        text = extract_text_pdf(downloaded_file)
    elif downloaded_file.endswith('.docx'):
        text = extract_text_docx(downloaded_file)
    elif downloaded_file.endswith('.txt'):
        text = extract_text_txt(downloaded_file)
    elif downloaded_file.endswith('.csv'):
        with open(downloaded_file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = None

    return text, downloaded_file
