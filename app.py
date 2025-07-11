import streamlit as st
from utils.gemini_llm import get_gemini_llm
from vector_dbs.dbs_retriever import db_retriever
from langchain.prompts import PromptTemplate
import os
import json
from utils.query_transformation import rewrite_query


# ----------------- CONFIG ------------------
st.set_page_config(page_title="Multi-Source RAG Assistant", layout="wide", initial_sidebar_state="expanded")

# ----------------- HEADER ------------------
st.markdown("<h1 style='color:#f63366'>🧠 Multi-Source RAG Assistant</h1>", unsafe_allow_html=True)
st.markdown("Ask questions about your projects using insights from Slack, Gmail and Drive.")


# ----------------- INFO DISCLAIMER ------------------
st.info(
    "The assistant’s responses may not be 100% accurate. "
    "For important decisions, please cross-check with official documents or your team.",
    icon="⚠️"
)

# ----------------- SIDEBAR ------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("- Source: Slack, Gmail, Drive, Reports")
    st.markdown("- Powered by Gemini Pro + LangChain")
    st.markdown("---")
    st.caption("ℹ️ Your chat history is saved only during the session.")

# ----------------- INIT ------------------
llm = get_gemini_llm()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.chat_input("Type your question here...")

# ----------------- CHAT HISTORY DISPLAY ------------------
for exchange in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(f"💬 **You:** {exchange['original_query']}")
        if exchange.get("rewritten_query"):
            st.markdown(f"🔁 **Rewritten:** `{exchange['rewritten_query']}`")
    with st.chat_message("assistant"):
        st.markdown(f"🧠 **Assistant:** {exchange['answer']}")


# ----------------- MAIN RAG LOGIC ------------------
if query:
    with st.chat_message("user"):
        st.markdown(query)

    # ----------------- LOAD PROJECT CONTEXT ------------------
    def load_report_tracker():
        with open("slack_project_reports/report_tracker.json", "r") as f:
            return json.load(f)

    report_tracker = load_report_tracker()

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

    project_key = detect_project_from_query(llm, query, report_tracker)

    with open("config/tracker_to_clickup_map.json", "r", encoding="utf-8") as f:
        tracker_to_clickup = json.load(f)

    clickup_key = tracker_to_clickup.get(project_key)

    def load_clickup_projects():
        with open("config/clickup_projects.json", "r", encoding="utf-8") as f:
            return json.load(f)

    clickup_data = load_clickup_projects()


    report_path = report_tracker.get(project_key, {}).get("report_path", "")
    full_report = ""

    if report_path and os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            full_report = f.read()

    
    clickup_context = ""
    if clickup_key and clickup_key in clickup_data:
        for t in clickup_data[clickup_key]:
            clickup_context += f"- {t['name']} | Status: {t['status']}\n"

    # ----------------- RETRIEVE CONTEXT ------------------
    
    from datetime import datetime 
    today = datetime.now().strftime("%B %d, %Y")
    ensemble_retriever = db_retriever()
    rewritten_query = rewrite_query(query, today)
    docs = ensemble_retriever.get_relevant_documents(rewritten_query)

    context = ""
    citations = []

    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")
        
        
        # project = meta.get("project", "unknown")

        # Add readable metadata block
        # context += f"📄 **Source:** {source} | **File:** {file_name} | **Project:** {project} | **Chunk:** {chunk_index}\n"
        context += doc.page_content + "\n\n"

        # Collect citation format
        # if source is not "unknown":
        #     citations.append(f"- {source}: {file_name} (Chunk {chunk_index})")

        if source.lower() == "slack":
            continue
        elif source.lower() == "gmail":
            subject = meta.get("subject", "unknown")
            sender = meta.get("sender", "unknown")
            citations.append(f"- Gmail: {sender} | subject: {subject}")
            context += f"📄 **Source:** {source} | **sender:** {sender} | **subject:** {subject}\n"

        elif source.lower() == "google_drive":
            file_name = meta.get("file_name", "unknown")
            chunk_index = meta.get("chunk_index", "N/A")
            citations.append(f"- {source}: {file_name} (Chunk {chunk_index})")
            context += f"📄 **Source:** {source} | **File:** {file_name} |**Chunk:** {chunk_index}\n"

    context += f"\n\n **Project Report:**\n{full_report}"
    context += f"\n\n **ClickUp Tasks Overview:**\n{clickup_context}"

    print(clickup_context)

    # ----------------- PROMPT GENERATION ------------------
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

    prompt = rag_prompt_template.format(context=context, question=query, today_date=today)

    # ----------------- CALL LLM ------------------
    response = llm.invoke(prompt)
    answer = response.content.strip()

    # ----------------- DISPLAY RESPONSE ------------------
    with st.chat_message("assistant"):
        st.markdown(f"🔁 **Rewritten Query for Better Retrieval:** `{rewritten_query}`")
        st.markdown(answer)

        with st.expander("📎 Citations"):
            for cite in citations:
                st.markdown(f"- {cite}")

    st.session_state.chat_history.append({
    "original_query": query,
    "rewritten_query": rewritten_query,
    "answer": answer
})



