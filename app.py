import streamlit as st
from utils.gemini_llm import get_gemini_llm
from vector_dbs.dbs_retriever import db_retriever

llm = get_gemini_llm()


from langchain.prompts import PromptTemplate

rag_prompt_template = PromptTemplate.from_template("""
You are an assistant answering questions using the following information from documents.

Use only the given context to answer. If unsure, say "I don't know."
                                                   
At the end, include citations for the sources you have used from given context to generate the response.        

Note: Do not add unknown or N/A to the response.                                                                               

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

    # 1. Retrieve documents
    ensemble_retriever = db_retriever()
    docs = ensemble_retriever.get_relevant_documents(query)

    # 2. Format context and citations from metadata
    context = ""
    citations = ""

    ## Fix this to include gmail & slack meta as well.
    for doc in docs:
        meta = doc.metadata
        file_name = meta.get("file_name", "unknown")
        chunk_index = meta.get("chunk_index", "N/A")
        source = meta.get("source", "unknown")

        context += f"[{file_name} | Chunk {chunk_index} | {source}]\n{doc.page_content}\n\n"

    prompt = rag_prompt_template.format(context=context, question=query)

    # 4. Run LLM
    response = llm.invoke(prompt)
    answer = response.content.strip()

    # Store in session
    st.session_state.chat_history.append((query, answer))

    with st.chat_message("assistant"):
        st.markdown(answer)