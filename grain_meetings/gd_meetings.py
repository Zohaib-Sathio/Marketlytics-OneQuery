from utils.google_embeddings import get_embeddings
from vector_dbs_pinecone.grain_meetings import chunk_and_store_meeting
from utils.drive_authentication import authenticate_drive
from utils.gd_files_tracking import load_gd_processed_ids, save_gd_processed_id
from utils.files_processing import extracted_text
from utils.gemini_llm import get_gemini_llm

import os

# Provide the folder ID you want to pull files from
TARGET_FOLDER_ID = "1SDPmZHumPcGGF4iE7dnSD66OAA8BtXiJ"

def list_files(service, folder_id, mime_type_filter=None):
    query = f"'{folder_id}' in parents"
    if mime_type_filter:
        query += f" and mimeType='{mime_type_filter}'"
        
    results = service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])

embeddings = get_embeddings()


def preprocess_with_llm(llm, raw_text, file_name):
    prompt = f"""
        You are a structured summarizer for Grain meeting summaries shared on Slack.
        Your job is to take raw, messy meeting summary text — which may include emojis, Slack markdown, timestamps, and links — and return a clean, context-rich, self-contained summary suitable for storage in a vector database used in RAG systems.
    
     "Clean the following meeting summary by:\n"
     "- Removing all special characters, links, and timestamps (like `t=123456`, `:arrow_forward:`, `<!date^...>`)\n"
     "- Normalizing formatting: replace bullet symbols (•, ☐) with plain text bullets (e.g., '-')\n"
     "- Preserve section headings like 'Key Takeaways', 'Discussion Topics', and 'Action Items'\n"
     "- Ensure the result is human-readable and can be used in semantic search\n"
     "- Do not use markdown — return the cleaned summary as plain text

TEXT:
{raw_text}
    """
    return llm.invoke(prompt)

embeddings = get_embeddings()
llm = get_gemini_llm()


def detect_project_from_meeting_metadata(llm, text, tracker):
        project_names = list(tracker.keys())
        project_list = "\n".join(f"- {name}" for name in project_names)
        prompt = f"""
Available text data:
"{text}"

Available projects:
{project_list}

You need to use the following text data to determine the name of the project from given projects list.

Return only the most relevant project name from the list. If none match, say "unknown".
"""
        response = llm.invoke(prompt)
        project_name = response.content.strip().lower()
        for key in tracker:
            if project_name == key.lower():
                return key
        return "unknown"

import json

def load_report_tracker():
        with open("slack_project_reports/report_tracker.json", "r") as f:
            return json.load(f)


def process_meetings_in_drive():
    service = authenticate_drive()
    print("✅ Authenticated with Google Drive")
    
    files = list_files(service, TARGET_FOLDER_ID)
    print(f"📂 Found {len(files)} files")
    
    report_tracker = load_report_tracker()

    for file in files:
        file_id = file['id']
        file_name = file['name']

        print(f"\n📄 Processing: {file_name} ({file_id})")

        try:
            # 1. Extract raw text
            raw_text, downloaded_file = extracted_text(file, service)


            project_name = detect_project_from_meeting_metadata(llm, raw_text[:350], report_tracker)
            print(project_name)


            # print(raw_text[:300])
            # print('Downloaded file: ', downloaded_file)

            if not raw_text.strip():
                print("⚠️ Empty content. Skipping.")
                continue

            # 2. Preprocess with LLM
            clean_text = preprocess_with_llm(llm, raw_text, file_name)
            # print(clean_text.content)

            # 3. Store in vector DB
            chunk_and_store_meeting(clean_text.content, {"source": "grain", "project_name": project_name})

            # 4. Track processed ID
            # save_gd_processed_id(file_id)
            print("✅ File processed and stored.")

        except Exception as e:
            print(f"❌ Failed to process {file_name}: {str(e)}")


if __name__ == "__main__":
    process_meetings_in_drive()
