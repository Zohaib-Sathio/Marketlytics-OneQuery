from utils.gemini_llm import get_gemini_llm
from vector_dbs.gmail_db import chunk_and_store_emails
from utils.gmail_authentication import authenticate_gmail
from utils.emails_id_tracking import load_processed_email_ids, save_processed_email_id

from langchain_core.prompts import ChatPromptTemplate

llm = get_gemini_llm()

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


from base64 import urlsafe_b64decode

def process_emails(service, max_results=5):

    processed_ids = load_processed_email_ids()

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
        save_processed_email_id(msg_id)
        metadata = {
                    "subject": subject,
                    "sender": sender
                }
        chunk_and_store_emails(response.content, metadata)

if __name__ == '__main__':
    service = authenticate_gmail()
    process_emails(service, max_results=15)
