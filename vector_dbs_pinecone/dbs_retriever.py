from langchain_pinecone import Pinecone as LangchainPinecone
from utils.google_embeddings import get_embeddings
from pinecone import Pinecone
from langchain.retrievers import EnsembleRetriever

import os
from dotenv import load_dotenv

load_dotenv()

def db_retriever(project_name=None):
    embeddings = get_embeddings()  # Gemini embeddings

    # Setup Pinecone client
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    # Index names (update if needed)
    DRIVE_INDEX = os.getenv("PINECONE_INDEX_NAME")  # e.g., "gdrive-index"
    MEETINGS_INDEX = os.getenv("MEETING_PINECONE_INDEX_NAME")  # e.g., "emails-index"

    index1 = pc.Index(DRIVE_INDEX)  
    index2 = pc.Index(MEETINGS_INDEX)

    vectorstore1 = LangchainPinecone(
        index=index1,
        embedding=embeddings,
        text_key="page_content"
    )
    vectorstore2 = LangchainPinecone(
        index=index2,
        embedding=embeddings,
        text_key="page_content"
    )

    retriever1 = vectorstore1.as_retriever(search_kwargs={"k": 3})
    retriever2 = vectorstore2.as_retriever(search_kwargs={"k": 3,})

    ensemble_retriever = EnsembleRetriever(
        retrievers=[retriever1, retriever2],
        weights=[0.5, 0.5]
    )

    return ensemble_retriever
