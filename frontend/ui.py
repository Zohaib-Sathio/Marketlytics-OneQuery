import streamlit as st
from langchain_chroma import Chroma
from langchain.retrievers import EnsembleRetriever
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Setup embeddings and LLM
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)
llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)

# Setup vector stores
CHROMA_DIR_1 = "vector_store/chroma"
CHROMA_DIR_2 = "vector_store/emails"
CHROMA_DIR_3 = "vector_store/slack_vector_db"

db1 = Chroma(persist_directory=CHROMA_DIR_1, embedding_function=embeddings)
db2 = Chroma(persist_directory=CHROMA_DIR_2, embedding_function=embeddings)
db3 = Chroma(persist_directory=CHROMA_DIR_3, embedding_function=embeddings)

retriever1 = db1.as_retriever(search_kwargs={"k": 3})
retriever2 = db2.as_retriever(search_kwargs={"k": 3})
retriever3 = db3.as_retriever(search_kwargs={"k": 3})

ensemble_retriever = EnsembleRetriever(
    retrievers=[retriever1, retriever2, retriever3],
    weights=[0.4, 0.2, 0.4]
)

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
    docs = ensemble_retriever.get_relevant_documents(query)

    # 2. Format context and citations from metadata
    context = ""
    citations = ""
    for doc in docs:
        meta = doc.metadata
        file_name = meta.get("file_name", "unknown")
        chunk_index = meta.get("chunk_index", "N/A")
        source = meta.get("source", "unknown")

        context += f"[{file_name} | Chunk {chunk_index} | {source}]\n{doc.page_content}\n\n"
        # citations += (
        #     f"- 📎 [**{file_name}**](https://drive.google.com/file/d/{file_id}/view) (Chunk #{chunk_index}) from `{source}`\n"
        #     if file_id else
        #     f"- 📄 {file_name} (Chunk #{chunk_index}) from `{source}`\n"
        # )

    # 3. Inject context into prompt
    prompt = rag_prompt_template.format(context=context, question=query)

    # 4. Run LLM
    # answer = llm.invoke(prompt)
    # answer += "\n\n#### 📚 Sources:\n" + citations
    response = llm.invoke(prompt)
    answer = response.content.strip()

    # Store in session
    st.session_state.chat_history.append((query, answer))

    with st.chat_message("assistant"):
        st.markdown(answer)