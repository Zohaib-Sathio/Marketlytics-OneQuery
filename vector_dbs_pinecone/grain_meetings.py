from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from langchain_pinecone import Pinecone as LangchainPinecone
from pinecone import Pinecone, ServerlessSpec
from utils.google_embeddings import get_embeddings
import os
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

# ENV Vars for Meetings Pinecone Index
MEETING_PINECONE_INDEX_NAME = os.getenv("MEETING_PINECONE_INDEX_NAME")  # separate index
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

# ✅ Pinecone client setup
pc = Pinecone(api_key=PINECONE_API_KEY)

embeddings = get_embeddings()

index = pc.Index(name=MEETING_PINECONE_INDEX_NAME)

def chunk_and_store_meeting(cleaned_text: str, metadata: dict):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

    chunks = text_splitter.split_text(cleaned_text)

    title_line = f"[This is the meeting summary for {metadata.get('project_name', 'Untitled')} project.]"

    documents = []
    for i, chunk in enumerate(chunks):
        chunk_meta = metadata.copy()
        chunk_meta.update({
            "chunk_index": i,
            "chunk_id": f"{metadata.get('project_name', 'unknown')}_chunk_{i}",
        })

        page_content = f"{title_line}\n\n{chunk}"
        documents.append(Document(page_content=page_content, metadata=chunk_meta))

    # ✅ Langchain wrapper for Pinecone
    vectorstore = LangchainPinecone(
        index=index,
        embedding=embeddings,
        text_key="page_content"
    )

    vectorstore.add_documents(documents)
    print(f"[✔] Stored {len(documents)} meeting chunks in Pinecone index: {MEETING_PINECONE_INDEX_NAME}")
