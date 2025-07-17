from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_pinecone import Pinecone as LangchainPinecone  # ✅ NEW PACKAGE
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from uuid import uuid4
import os

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# ✅ Correct initialization
pc = Pinecone(api_key=PINECONE_API_KEY)

# ✅ Safe index creation
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region=PINECONE_ENVIRONMENT
        )
    )

# ✅ Correct way to get index
index = pc.Index(name=PINECONE_INDEX_NAME)

def chunk_and_store_gd(text: str, metadata: dict, embeddings: Embeddings):
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = splitter.split_text(text)

    documents = []
    for i, chunk in enumerate(chunks):
        chunk_meta = metadata.copy()
        chunk_meta.update({
            "chunk_index": i,
            "chunk_id": f"{metadata['file_id']}_chunk_{i}"
        })
        documents.append(Document(page_content=chunk, metadata=chunk_meta))

    # ✅ Langchain-compatible wrapper from the new package
    vectorstore = LangchainPinecone(
        index=index,
        embedding=embeddings,
        text_key="page_content"
    )

    vectorstore.add_documents(documents)
    print(f"[✔] Stored {len(documents)} chunks in Pinecone index: {PINECONE_INDEX_NAME}")
