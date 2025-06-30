import streamlit as st
from utils.gemini_llm import get_gemini_llm
from vector_dbs.dbs_retriever import db_retriever

llm = get_gemini_llm()


from langchain.prompts import PromptTemplate

rag_prompt_template = PromptTemplate.from_template("""
You are an assistant answering questions using the following information from documents.

Use only the given context to answer. If unsure, say "I don't know."
                                                   
At the end, include citations for the sources you have used from given context to generate the response. Also mention the source as well with them.       

Note: Do not add unknown or N/A to the citations.                                                                               

Context:
{context}

Question:
{question}
""")

# Streamlit App UI
st.set_page_config(page_title="Multi-Source RAG Assistant", layout="wide")
st.title("🧠 Multi-Source RAG Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Query box
query = st.chat_input("Ask your question...")

# Display history
for user_input, bot_response in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(bot_response)

if query:
    with st.chat_message("user"):
        st.markdown(query)

    
    import json

    def load_project_catalog():
        with open("slack_project_reports/project_catalog.json", "r") as f:
            return json.load(f)

    project_catalog = load_project_catalog()

    def detect_project_from_query(llm, query, project_catalog):
        project_names = [v["name"] for v in project_catalog.values()]
        project_list = "\n".join(f"- {name}" for name in project_names)

        prompt = f"""
    You are an assistant that determines which project a user is referring to in their question.

    Here is the user query:
    "{query}"

    Here are the available projects:
    {project_list}

    Return only the most relevant project name from the list. If none match, say "unknown".
    """

        response = llm.invoke(prompt)
        project_name = response.content.strip().lower()

        # Normalize and find matching key
        for key, data in project_catalog.items():
            if project_name == data["name"].lower():
                return key
        return "unknown"
    
    project_key = detect_project_from_query(llm, query, project_catalog)
    print(f"product key: {project_key}")
    project_data = project_catalog.get(project_key)
    report_path = ''

    if project_key != "unknown":
        report_path = project_data["report_path"]

    full_report = ''
    if report_path:
        with open(report_path, "r", encoding="utf-8") as f:
            full_report = f.read()

    # 1. Retrieve documents
    ensemble_retriever = db_retriever()
    docs = ensemble_retriever.get_relevant_documents(query)

    # 2. Format context and citations from metadata
    context = ""
    citations = ""

    ## Fix this to include gmail & slack meta as well.
        ## Update the logic separately for all three source to handle metadata according to them
    for doc in docs:
        meta = doc.metadata
        slack_channel_project = meta.get("project", "unknown")
        file_name = meta.get("file_name", "unknown")
        chunk_index = meta.get("chunk_index", "N/A")
        source = meta.get("source", "unknown")

        if source.lower() == "slack":
            continue
        elif source.lower() == "gmail":
        #     "source": "gmail",
        #     "subject": subject,  # Last message's subject
        #     "sender": sender,     # Last message's sender
        #     "email_id": thread_id
            continue
        elif source.lower() == "google_drive":
            # "source": "google_drive",
            # "file_name": file["name"],
            # "file_id": file["id"]
            continue

        context += f"[{slack_channel_project}{file_name} | Chunk {chunk_index} | {source}]\n{doc.page_content}\n\n"

    context += f" here is also Project Progess Report (if there is any): {full_report}"

    print(context)
    print(len(context))
    prompt = rag_prompt_template.format(context=context, question=query)

    # 4. Run LLM
    response = llm.invoke(prompt)
    answer = response.content.strip()

    # Store in session
    st.session_state.chat_history.append((query, answer))

    with st.chat_message("assistant"):
        st.markdown(answer)