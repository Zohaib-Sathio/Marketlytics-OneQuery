# main.py

import os
import logging
from server import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from utils.gemini_llm import get_gemini_llm
from vector_dbs_pinecone.dbs_retriever import db_retriever
from utils.storage_manager import GCSStorageManager
from langchain.prompts import PromptTemplate

# -------- Setup --------
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
llm = get_gemini_llm()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def handle_query(payload: QueryRequest):
    query = payload.query

    gcs_key_path = os.getenv("GCS_KEY_PATH")
    if not gcs_key_path:
        raise HTTPException(status_code=500, detail="Missing GCS_KEY_PATH environment variable")

    gcs = GCSStorageManager("marketlytics-onequery", gcs_key_path)

    def load_report_tracker():
        try:
            return gcs.load_json("slack_project_reports/report_tracker.json")
        except Exception as e:
            logger.warning(f"Failed to load tracker from GCS: {e}")
            return {}

    def detect_project_from_query(llm, query, tracker):
        project_names = list(tracker.keys())
        prompt = f"""
User query:
"{query}"

Available projects:
{chr(10).join(f"- {name}" for name in project_names)}

Return only the most relevant project name from the list. If none match, say "unknown".
"""
        response = llm.invoke(prompt)
        project_name = response.content.strip().lower()
        for key in tracker:
            if project_name == key.lower():
                return key
        return "unknown"

    report_tracker = load_report_tracker()
    project_key = detect_project_from_query(llm, query, report_tracker)

    try:
        tracker_to_clickup = gcs.load_json("config/tracker_to_clickup_map.json")
    except Exception as e:
        logger.error(f"Could not load tracker_to_clickup_map.json: {e}")
        tracker_to_clickup = {}

    clickup_key = tracker_to_clickup.get(project_key, "")
    clickup_data = gcs.load_json("clickup_data/clickup_projects.json")

    report_path = report_tracker.get(project_key, {}).get("report_path", "")
    full_report = gcs.load_text(report_path) if report_path else ""

    clickup_context = ""
    if clickup_key and clickup_key in clickup_data:
        for t in clickup_data[clickup_key]:
            clickup_context += f"- {t['name']} | Status: {t['status']}\n"

    # Retrieve from DB
    today = datetime.now().strftime("%B %d, %Y")
    ensemble_retriever = db_retriever(project_key)
    docs = ensemble_retriever.get_relevant_documents(query)

    context = ""
    citations = []

    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")

        if source.lower() == "gmail":
            subject = meta.get("subject", "unknown")
            sender = meta.get("sender", "unknown")
            citations.append(f"- Gmail: {sender} | subject: {subject}")
            context += f"📄 Gmail | Sender: {sender} | Subject: {subject}\n"
        elif source.lower() == "google_drive":
            file_name = meta.get("file_name", "unknown")
            chunk_index = meta.get("chunk_index", "N/A")
            citations.append(f"- Drive: {file_name} (Chunk {chunk_index})")
            context += f"📄 Drive | File: {file_name} | Chunk: {chunk_index}\n"
        elif source.lower() == "grain":
            project_name = meta.get("project_name", "unknown")
            citations.append(f"- Grain: {project_name}")
            context += f"📄 Grain | Project name: {project_name}\n"

        context += doc.page_content + "\n\n"

    context += f"\n\n**Project Report:**\n{full_report}"
    context += f"\n\n**ClickUp Tasks Overview:**\n{clickup_context}"

    # Prompts
    rag_prompt_template = PromptTemplate.from_template("""
You are an expert assistant helping answer questions based on multiple sources: Slack, Gmail, Drive, Reports.

Instructions:
- Use only the provided context.
- Be concise and fact-based.
- Include date references if possible.

Today’s date: {today_date}

Context:
{context}

Question:
{question}
""")

    reasoning_prompt_template = PromptTemplate.from_template("""
You are a reasoning agent that re-evaluates the assistant's response.

Inputs:
- Original Question: {question}
- Context: {context}
- Assistant's Answer: {answer}

Return a better version if needed, otherwise return as-is.

Today’s date: {today_date}
""")

    prompt = rag_prompt_template.format(context=context, question=query, today_date=today)
    raw_response = llm.invoke(prompt).content.strip()

    reasoning_prompt = reasoning_prompt_template.format(
        question=query,
        context=context,
        answer=raw_response,
        today_date=today
    )
    improved_response = llm.invoke(reasoning_prompt).content.strip()

    return {
        "project_detected": project_key,
        "answer": improved_response,
        "citations": citations
    }
