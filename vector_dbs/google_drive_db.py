from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_chroma import Chroma 

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from uuid import uuid4



CHROMA_DIR = "vector_store/google_drive"

def chunk_and_store_gd(text, metadata, embeddings):
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = splitter.split_text(text)

    documents = []
    for i, chunk in enumerate(chunks):
        chunk_meta = metadata.copy()
        chunk_meta.update({
            "chunk_index": i,
            "chunk_id": str(uuid4()),  # useful for deduplication or updates
        })
        documents.append(Document(page_content=chunk, metadata=chunk_meta))

    if not os.path.exists(CHROMA_DIR):
        db = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_DIR)
    else:
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        db.add_documents(documents)
