import streamlit as st
from langchain_chroma import Chroma
from langchain.retrievers import EnsembleRetriever
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
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

db1 = Chroma(persist_directory=CHROMA_DIR_1, embedding_function=embeddings)
db2 = Chroma(persist_directory=CHROMA_DIR_2, embedding_function=embeddings)

retriever1 = db1.as_retriever(search_kwargs={"k": 3})
retriever2 = db2.as_retriever(search_kwargs={"k": 3})

ensemble_retriever = EnsembleRetriever(
    retrievers=[retriever1, retriever2],
    weights=[0.7, 0.3]
)

# Setup memory + chain
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=ensemble_retriever,
    memory=memory
)

# Streamlit App UI
st.set_page_config(page_title="Multi-Source RAG Assistant", layout="wide")
st.title("🧠 Multi-Source RAG Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Query box
query = st.chat_input("Ask your question...")

# Display history
for i, (user_input, bot_response) in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(bot_response)

if query:
    with st.chat_message("user"):
        st.markdown(query)

    # Run QA chain
    response = qa_chain.invoke({"question": query})
    result = response['answer']

    # Store in session
    st.session_state.chat_history.append((query, result))

    with st.chat_message("assistant"):
        st.markdown(result)

# Optional ingestion button
# if st.sidebar.button("🔁 Ingest from Google Drive"):
#     st.sidebar.write("Ingesting documents...")
#     # process_drive()
#     st.sidebar.success("Ingestion completed!")
