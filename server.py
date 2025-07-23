from fastapi  import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
import os
from dotenv import load_dotenv
import logging

from utils.gemini_llm import get_gemini_llm
from vector_dbs_pinecone.dbs_retriever import db_retriever
from langchain.prompts import PromptTemplate
from utils.storage_manager import GCSStorageManager
from datetime import datetime

load_dotenv(override=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ---------------- Request Schema ----------------
class QueryRequest(BaseModel):
    query: str

# ---------------- Response Schema ----------------
class QueryResponse(BaseModel):
    project_key: str
    improved_answer: str
    citations: List[str]

# ---------------- Helper Functions ----------------

def load_report_tracker(gcs):
    try:
        return gcs.load_json("slack_project_reports/report_tracker.json")
    except Exception as e:
        logger.warning(f"Failed to load tracker from GCS: {e}")
        return {}

def detect_project_from_query(llm, query, tracker):
    project_names = list(tracker.keys())
    project_list = "\n".join(f"- {name}" for name in project_names)
    prompt = f"""
User query:
"{query}"

Available projects:
{project_list}

Return only the most relevant project name from the list. If none match, say "unknown".
"""
    response = llm.invoke(prompt)
    project_name = response.content.strip().lower()
    for key in tracker:
        if project_name == key.lower():
            return key
    return "unknown"

def load_clickup_projects(gcs):
    return gcs.load_json("clickup_data/clickup_projects.json")

# ---------------- Main Query Endpoint ----------------
@app.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    print('test1')
    query = request.query
    today = datetime.now().strftime("%B %d, %Y")

    # Load LLM and GCS
    llm = get_gemini_llm()
    gcs_key_path = os.getenv("GCS_KEY_PATH")
    if not gcs_key_path:
        raise ValueError("Missing GCS_KEY_PATH environment variable")
    gcs = GCSStorageManager("marketlytics-onequery", gcs_key_path)
    print('test2')

    report_tracker = load_report_tracker(gcs)
    project_key = detect_project_from_query(llm, query, report_tracker)

    try:
        tracker_to_clickup = gcs.load_json("config/tracker_to_clickup_map.json")
    except Exception as e:
        logger.error(f"Could not load tracker_to_clickup_map.json: {e}")
        tracker_to_clickup = {}

    clickup_key = tracker_to_clickup.get(project_key)
    clickup_data = load_clickup_projects(gcs)

    report_path = report_tracker.get(project_key, {}).get("report_path", "")
    full_report = ""
    if report_path:
        try:
            full_report = gcs.load_text(report_path)
        except Exception as e:
            logger.warning(f"Failed to load report: {e}")

    clickup_context = ""
    if clickup_key and clickup_key in clickup_data:
        for t in clickup_data[clickup_key]:
            clickup_context += f"- {t['name']} | Status: {t['status']}\n"
    
    print('test3')

    # RAG Retrieval
    ensemble_retriever = db_retriever(project_key)
    docs = ensemble_retriever.get_relevant_documents(query)
    print('test4')

    context = ""
    citations = []

    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")
        context += doc.page_content + "\n\n"

        if source.lower() == "gmail":
            subject = meta.get("subject", "unknown")
            sender = meta.get("sender", "unknown")
            citations.append(f"- Gmail: {sender} | subject: {subject}")
            context += f"📄 **Source:** {source} | **sender:** {sender} | **subject:** {subject}\n"
        elif source.lower() == "google_drive":
            file_name = meta.get("file_name", "unknown")
            chunk_index = meta.get("chunk_index", "N/A")
            citations.append(f"- {source}: {file_name} (Chunk {chunk_index})")
            context += f"📄 **Source:** {source} | **File:** {file_name} |**Chunk:** {chunk_index}\n"
        elif source.lower() == "grain":
            project_name = meta.get("project_name")
            citations.append(f"- {source}: {project_name}")
            context += f"📄 **Source:** {source} | **Project name:** {project_name}\n"

    context += f"\n\n **Project Report:**\n{full_report}"
    context += f"\n\n **ClickUp Tasks Overview:**\n{clickup_context}"

    # Prompt Templates
    rag_prompt_template = PromptTemplate.from_template("""
You are an expert assistant helping answer questions based on multiple sources: Slack messages, Gmail threads, Google Drive files, and an up-to-date project progress report.

Instructions:
- Use only the provided context.
- If you don’t know the answer, say "I don't know."
- Favor the most recent updates or clarifications.
- Prefer Slack for real-time status, Gmail for approvals/discussions, Drive for formal docs and ClickUp for tasks update.
- Use the **Project Progress Report** as the reliable summary of overall status.
- Use ClickUp tasks data to just know the progress on tasks.                                                       
- Mention the **date** of updates if possible.
- **Today’s date is {today_date}. Use this to evaluate how recent updates are.**                                                         
- End with a short citation list of the sources you used.

Context:
{context}

Question:
{question}
""")
    reasoning_prompt_template = PromptTemplate.from_template("""
You are a reasoning agent that re-evaluates the assistant's response using the provided context and user question.

Inputs:
- Original Question: {question}
- Provided Context: {context}
- Assistant's Answer: {answer}

Instructions:
- Assess if the assistant's answer fully and accurately addresses the question using the context.
- If the answer is incomplete, incorrect, or lacks relevance, revise it.
- If the answer is already strong and accurate, return it as-is.
- If the answer includes some extra info relevant to the query then let it be.
- Do not include reasoning, analysis, or explanation.
- Only return the final answer that should be shown to the user.
- Respond back with bullet point output or any other structure which is easy to read and delivers the information.

Today’s date: {today_date}
""")

    prompt = rag_prompt_template.format(context=context, question=query, today_date=today)
    response = llm.invoke(prompt)
    answer = response.content.strip()

    reasoning_prompt = reasoning_prompt_template.format(
        question=query,
        context=context,
        answer=answer,
        today_date=today
    )
    reasoning_response = llm.invoke(reasoning_prompt)
    improved_answer = reasoning_response.content.strip()

    return QueryResponse(
        project_key=project_key,
        improved_answer=improved_answer,
        citations=citations
    )
