import streamlit as st
from utils.gemini_llm import get_gemini_llm
from vector_dbs_pinecone.dbs_retriever import db_retriever
from langchain.prompts import PromptTemplate
# from utils.query_transformation import rewrite_query


# ----------------- CONFIG ------------------
st.set_page_config(page_title="Multi-Source RAG Assistant", layout="wide", initial_sidebar_state="expanded")

# ----------------- HEADER ------------------
st.markdown("<h1 style='color:#f63366'>🧠 Multi-Source RAG Assistant</h1>", unsafe_allow_html=True)
st.markdown("Ask questions about your projects using insights from Slack, Gmail and Drive.")


# ----------------- INFO DISCLAIMER ------------------
st.info(
    "The assistant’s responses may include old pending tasks due to lack of completion update. "
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
        st.markdown(f"**Assistant:** {exchange['improved_answer']}")


# ----------------- MAIN RAG LOGIC ------------------
if query:
    with st.chat_message("user"):
        st.markdown(query)
    from utils.storage_manager import GCSStorageManager

    gcs = GCSStorageManager("marketlytics-onequery", "config/gcs_account_key.json")


    # ----------------- LOAD PROJECT CONTEXT ------------------
    def load_report_tracker():
        try:
            return gcs.load_json("slack_project_reports/report_tracker.json")
        except Exception as e:
            print(f"⚠️ Failed to load tracker from GCS: {e}")
            return {}

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
    print(f"project name: {project_key}")

    try:
        tracker_to_clickup = gcs.load_json("config/tracker_to_clickup_map.json")
    except Exception as e:
        print("❌ Could not load tracker_to_clickup_map.json:", e)
        tracker_to_clickup = {}

    clickup_key = tracker_to_clickup.get(project_key)

    def load_clickup_projects():
        from utils.storage_manager import GCSStorageManager
        gcs = GCSStorageManager("marketlytics-onequery", "config/gcs_account_key.json")
        return gcs.load_json("clickup_data/clickup_projects.json")

    clickup_data = load_clickup_projects()


    report_path = report_tracker.get(project_key, {}).get("report_path", "")
    full_report = ""

    
    if report_path:
        try:
            full_report = gcs.load_text(report_path)
            print("Report path: ", report_path)
            print(full_report)
        except Exception as e:
            print(f"⚠️ Failed to load report from GCS: {e}")

    
    clickup_context = ""
    if clickup_key and clickup_key in clickup_data:
        for t in clickup_data[clickup_key]:
            clickup_context += f"- {t['name']} | Status: {t['status']}\n"

    # ----------------- RETRIEVE CONTEXT ------------------
    
    from datetime import datetime 
    today = datetime.now().strftime("%B %d, %Y")
    ensemble_retriever = db_retriever(project_key)
    # rewritten_query = rewrite_query(query, today)
    docs = ensemble_retriever.get_relevant_documents(query)
    print("Length of the docs: ", len(docs))

    context = ""
    citations = []

    for doc in docs:
        print(doc)
        print("\n", "*"*30)
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
        elif source.lower() == "grain":
            project_name = meta.get("project_name")
            citations.append(f"- {source}: {project_name}")
            context += f"📄 **Source:** {source} | **Project name:** {project_name}\n"

    context += f"\n\n **Project Report:**\n{full_report}"
    context += f"\n\n **ClickUp Tasks Overview:**\n{clickup_context}"


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

    # ----------------- CALL LLM ------------------
    response = llm.invoke(prompt)
    answer = response.content.strip()

    reasoning_prompt = reasoning_prompt_template.format(
    question=query,
    context=context,
    answer=answer,
    today_date=today 
    )
    print("Context: ", context)

    reasoning_response = llm.invoke(reasoning_prompt)
    improved_answer = reasoning_response.content.strip()


    # ----------------- DISPLAY RESPONSE ------------------
    with st.chat_message("assistant"):
        st.markdown("🧠 **Initial Answer:**")
        st.markdown(answer)
        st.markdown("---")
        st.markdown("**After Reasoning:**")
        st.markdown(improved_answer)

        with st.expander("📎 Citations"):
            for cite in citations:
                st.markdown(f"- {cite}")

    st.session_state.chat_history.append({
    "original_query": query,
    # "rewritten_query": rewritten_query,
    "answer": answer,
    "improved_answer": improved_answer
})



