from utils.gemini_llm import get_gemini_llm
from utils.google_embeddings import get_embeddings
from vector_dbs.google_drive_db import chunk_and_store_gd
from utils.drive_authentication import authenticate_drive
from utils.gd_files_tracking import load_gd_processed_ids, save_gd_processed_id
from utils.files_processing import extracted_text

import os

def list_files(service, mime_type_filter=None):
    query = f"mimeType='{mime_type_filter}'" if mime_type_filter else ""
    results = service.files().list(q=query, pageSize=10, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])


embeddings = get_embeddings()

def process_drive():
    service = authenticate_drive()

    files = list_files(service)

    processed_ids = load_gd_processed_ids()

    for file in files:
        file_id =  file['id']
        file_name = file['name']
        if file_id in processed_ids:
            print(f"Skipping already processed file : {file_name} {file_id}")
            continue
        

        if file['name'].endswith('.pdf') or file['name'].endswith('.docx') or file['name'].endswith('.txt'):
            try:
                text, local_file  = extracted_text(file, service)
                print("Content extracted!")

                if not text.strip(): 
                    continue

                metadata = {
                    "source": "google_drive",
                    "file_name": file["name"],
                    "file_id": file["id"]
                }

                chunk_and_store_gd(text, metadata, embeddings)

                save_gd_processed_id(file_id)

                if os.path.exists(local_file):
                    os.remove(local_file)
                    print(f"Deleted local file: {local_file}")
                
            except Exception as e:
                print(f"[!] Failed on {file['name']}: {e}")


llm = get_gemini_llm()


if __name__ == "__main__":
    process_drive()