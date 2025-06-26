from utils.gemini_llm import get_gemini_llm
from vector_dbs.gmail_db import chunk_and_store_emails
from utils.gmail_authentication import authenticate_gmail
from utils.emails_id_tracking import load_processed_email_ids, save_processed_email_id

from langchain_core.prompts import ChatPromptTemplate

llm = get_gemini_llm()
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a precise AI assistant for processing email conversations. "
     "Your goal is to generate dense, context-rich, self-contained summaries for storage in a vector database used for semantic search and retrieval."),
    
    ("human",
     "Given the following email content, first determine whether it is a **single email** or a **thread of multiple messages**:\n\n"
     "- If it is a **single email**, extract the useful information including:\n"
     "  - Subject\n  - Sender and Recipient\n  - Key content, decisions, and action points\n\n"
     "- If it is a **thread**, build a **progressive summary** from oldest to newest message. Capture:\n"
     "  - Who said what and when (include sender names, don't include exact timestamps)\n"
     "  - How the conversation evolved over time\n"
     "  - What questions were raised and answered\n"
     "  - Any key decisions, agreements, tasks, or unresolved points\n\n"
     "  - then make a detailed report of all conversations whatever was discussed in them."
     "Do not use markdown. Write in plain text. Your output should be coherent, self-contained, and useful even without access to the original thread.\n\n"
     "Email Content:\n{email_body}")
])


def extract_email_insights(email_text):
    chain = prompt | llm
    return chain.invoke({"email_body": email_text})


def extract_text_from_parts(parts):
    for part in parts:
        if part['mimeType'] == 'text/plain':
            data = part['body'].get('data')
            if data:
                return urlsafe_b64decode(data).decode('utf-8')
        elif 'parts' in part:
            # Recurse into nested parts
            result = extract_text_from_parts(part['parts'])
            if result:
                return result
    return ""

def get_header(headers, name):
    return next((h['value'] for h in headers if h['name'] == name), '')



from base64 import urlsafe_b64decode
def process_email_threads(service, max_results=1):
    processed = load_processed_email_ids()

    threads = service.users().threads().list(userId='me', maxResults=max_results).execute().get('threads', [])
    
    for th in threads:
        thread_id = th['id']
        if thread_id in processed:
            print("Already processed email.")
            continue  # skip already handled threads

        thread = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
        
        thread_text = ''

        messages = thread.get('messages', [])
        for msg in messages:
            payload = msg['payload']
            parts = payload.get('parts', [])
            msg_text = extract_text_from_parts(parts)
            headers = payload.get('headers', [])
            subject = get_header(headers, 'Subject')
            print('Subject: ', subject)
            sender = get_header(headers, 'From')
            thread_text += f"Subject: {subject}\nFrom: {sender}\n\n{msg_text}\n\n{'='*50}\n\n"
            

        # print("🧠 Full Thread Text:\n", thread_text)

        response = extract_email_insights(thread_text)
        # print("✅ LLM Extracted Insights:\n", response.content)

        metadata = {
            "subject": subject,  # Last message's subject
            "sender": sender,     # Last message's sender
            "email_id": thread_id
        }

        chunk_and_store_emails(response.content, metadata)
        save_processed_email_id(thread_id)
    

if __name__ == '__main__':
    service = authenticate_gmail()
    process_email_threads(service, max_results=3)
